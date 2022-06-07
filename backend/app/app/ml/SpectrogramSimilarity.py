from typing import Optional, List, Any, Union

import shelve
from datetime import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd

# import psycopg2
import torch
from celery.utils.log import get_task_logger
from tqdm import tqdm

from app.ml.models import MODEL_DICT
from app.db.session import session_scope

# from app.spotify.spectrogram import download_spectrogram, upload_spectrogram
# from app.spotify.spotify_mux import SpotifyMux
# from app.models import ML_Model
# from app import crud, schemas
from app.core.config import settings


shelve_path = "/app/app/ml_model/sim_shelf"
cuda = torch.cuda.is_available()

logger = get_task_logger(__name__)
ITERSIZE = 70


class SpectrogramSimilarity:
    def __init__(
        self,
        model,
        model_id: str = None,
        model_type: str = None,
        date_trained: datetime = None,
        epochs: int = None,
        extra_metadata: str = None,
    ):
        self.cuda = torch.cuda.is_available()
        print("gpu available :", self.cuda)
        self.device = torch.device("cuda" if self.cuda else "cpu")
        self.model = model.to(self.device)
        self.shelve = None
        self.last_tid = None
        self.last_feat = None
        self.model_id = model_id
        self.model_type = model_type
        self.date_trained = date_trained
        self.epochs = epochs
        self.extra_metadata = extra_metadata

    @classmethod
    def load(cls, saved_model_path: str):

        cuda = torch.cuda.is_available()
        model_dict = torch.load(
            saved_model_path, map_location=torch.device("cuda" if cuda else "cpu")
        )
        model_name = model_dict["model_name"]

        model_id = Path(saved_model_path).stem
        model_config = model_id.split("_")
        model_type = model_config[0]
        date_trained = datetime.fromisoformat(model_config[1])
        epochs = int(model_config[2])
        extra_metadata = model_config[-1] if len(model_config) > 3 else None

        model_class = MODEL_DICT[model_type]
        model = model_class(model_dict["shape"][1])  # output dims
        model.load_state_dict(model_dict["model"])

        return SpectrogramSimilarity(
            model, model_id, model_type, date_trained, epochs, extra_metadata
        )

    def calculate_distance(
        self,
        t1_feats: Union[np.ndarray, torch.Tensor],
        t2_feats: Union[np.ndarray, torch.Tensor],
        distance_type: Optional[str] = settings.DISTANCE_TYPE,
    ) -> torch.Tensor:
        if isinstance(t1_feats, np.ndarray):
            t1_feats = torch.Tensor(t1_feats).to(self.device).float()
        if isinstance(t2_feats, np.ndarray):
            t2_feats = torch.Tensor(t2_feats).to(self.device).float()

        with torch.no_grad():
            if distance_type == "euclidean":
                try:
                    return ((t1_feats - t2_feats) ** 2).sum()
                except Exception as e:
                    raise (e)
            # if tid1 != self.last_tid:
            # self.last_tid = tid1
            # self.last_feat = self.shelve[tid1]
            # return torch.sum((self.last_feat - self.shelve[tid2]) ** 2)

    def get_features(self, data: np.ndarray) -> torch.Tensor:
        self.model.eval()
        with torch.no_grad():
            if data.ndim == 2:
                data = np.expand_dims(data, 0)
            data = torch.Tensor(data).to(self.device).float()
            return self.model.output_features(data).to(self.device)

    def get_predictions(
        self, data: Union[np.ndarray, List[np.ndarray]]
    ) -> torch.Tensor:
        if isinstance(data, list):
            # if isinstance(data[0], list):
            #     data = [np.array(x) for x in data]
            data = np.array(data)

        self.model.eval()
        with torch.no_grad():
            data = torch.Tensor(data).to(self.device).float()
            return self.model.output_probabilities(data).to(self.device)

    def open_shelve(self, sp):
        self.shelve = shelve.open(sp)

    def init_shelve(self, n=150, m=500):
        with db.engine.connect() as conn:
            query = f"""
                (select track_id
                    from stream_counts sc
                    join spectrograms sp
                    using (track_id)
                    where sp.track_id is not null
                    order by playcount desc
                    limit {n/2})

                    UNION

                (select track_id
                    from playlists_tracks pt
                    join playlists pl
                    on pt.playlist_id=pl.id
                    join spectrograms sp
                    using (track_id)
                    where sp.track_id is not null
                    AND track_id is not null
                        and pl.owner_id = 'spotify'
                    group by track_id
                    order by count(distinct playlist_id) desc
                    limit {n/2})

                    UNION

                (SELECT track_id
                    FROM model_results
                    join spectrograms sp
                    using (track_id)
                    where sp.track_id is not null
                    group by track_id
                    having max(probability) > 0.3 and max(playcount) < 500000
                    order by max(probability) desc, max(playcount/probability) desc
                    limit {m})
            """
            to_get = set(pd.read_sql(query, conn)["track_id"].values) - set(
                self.shelve.keys()
            )
            for track_id in tqdm(to_get):
                r = conn.execute(
                    f"""
                    SELECT track_id
                           , spectrogram
                    from spectrograms k
                    where track_id = '{track_id}'
                    limit 1
                    """
                )
                row = r.fetchone()
                with BytesIO(row[1].tobytes()) as f:
                    # Precomputing features instead of spectrogram saves time
                    self.shelve[row[0]] = self.get_features(np.load(f))

    def close_shelve(self):
        self.shelve.close()

    def calc_similarity_between_pairs(self, list_of_songs):
        list_of_songs = list(list_of_songs)
        matrix = [
            [0 for i in range(len(list_of_songs))] for j in range(len(list_of_songs))
        ]
        for i in range(len(list_of_songs)):
            for j in range(i, len(list_of_songs)):
                if i != j:
                    song_i = list_of_songs[i][-1]
                    song_j = list_of_songs[j][-1]
                    if self.cuda:
                        distance = self.calculate_distance(song_i, song_j).cpu()
                    distance = distance.numpy()
                    matrix[i][j] = distance
        matrix = np.array(matrix)
        max_val = np.max(matrix)
        min_val = np.min(matrix)
        print(matrix)
        matrix = (matrix - min_val) / (max_val - min_val)
        return matrix


spec_model = SpectrogramSimilarity.load(saved_model_path=settings.MODEL_WEIGHTS)


# @app.task(bind=True)
# def test_similarity(n=150, m=1000):
#     t = SpectrogramSimilarity.load(
#         "/app/models/2019-11-25-01_26_chunk-2_epochs-100_name-CNN_SpectrogramV2_.tar"
#     )
#     with shelve.open(shelve_path) as features:
#         print("Starting Query...")
#         with db.engine.connect() as conn:
#             with conn.execution_options(postgresql_with_hold=True).connection.cursor(
#                 "similarity_curse"
#             ) as cursor:
#                 cursor.itersize = ITERSIZE
#                 cursor.execute(
#                     f"""
#                     SELECT track_id,
#                            spectrogram
#                     from (select s.track_id
#                             from playlists_tracks pt
#                             left join spectrograms s
#                             using (track_id)
#                             left join playlists p
#                             on pt.playlist_id = p.id
#                             where s.track_id is not null
#                             and p.owner_id = 'spotify'
#                             group by s.track_id
#                             order by count(distinct pt.playlist_id) desc
#                     ) n
#                     join spectrograms k
#                     using (track_id)
#                     limit {n}
#                 """
#                 )
#                 print("Query finished, fetching sources...")
#                 np_specs = []
#                 n_ = 0
#                 with tqdm(total=n) as tq:
#                     try:
#                         for row in cursor:
#                             with BytesIO(row[1].tobytes()) as f:
#                                 res = np.load(f)
#                                 # Precomputing features instead of spectrogram saves time
#                                 np_specs.append(row[0])
#                                 features[row[0]] = t.get_features(res)
#                                 tq.update(1)
#                                 n_ += 1
#                     except psycopg2.ProgrammingError:
#                         pass
#         with db.engine.connect() as conn:
#             with conn.execution_options(postgresql_with_hold=True).connection.cursor(
#                 "similarity_curse_2"
#             ) as cursor:
#                 cursor.itersize = ITERSIZE
#                 cursor.execute(
#                     f"""
#                     SELECT track_id,
#                            spectrogram
#                     from (
#                         SELECT track_id
#                         FROM model_results
#                         group by track_id
#                         having max(probability) > 0.3 and max(playcount) < 500000
#                         order by max(probability) desc, max(playcount/probability) desc
#                     ) n
#                     join spectrograms k
#                     using (track_id)
#                     limit {m}
#                 """
#                 )
#                 print("Query finished, fetching targets...")
#                 np_specs2 = []
#                 m_ = 0
#                 with tqdm(total=m) as tq:
#                     try:
#                         for row in cursor:
#                             with BytesIO(row[1].tobytes()) as f:
#                                 res = np.load(f)
#                                 np_specs2.append(row[0])
#                                 features[row[0]] = t.get_features(res)
#                                 tq.update(1)
#                                 m_ += 1
#                     except psycopg2.ProgrammingError:
#                         pass
#             features.close()
#         t.open_shelve(shelve_path)
#         print("fetch finished, similarity...")
#         sims = []
#         with tqdm(total=n_ * m_) as tq:
#             for tid1 in np_specs:
#                 for tid2 in np_specs2:
#                     tq.update(1)
#                     if tid1 != tid2:
#                         n = float(t.calculate_distance(tid1, tid2))
#                         sims.append((tid1, tid2, n))
#         print("sim_finished!")
#         sims = pd.DataFrame(sims, columns=("source", "target", "distance"))
#     # TODO: rewrite this correctly so that src,tgt,dist is placed in
#     # tracks_distances table once, not recalculated every time.
#     with db.engine.connect() as conn:
#         conn.execute(f"DROP TABLE IF EXISTS {db.RECOMMENDATIONS_BUCKET}_new;")
#         n = 20_000  # chunk row size
#         for i in tqdm(range(0, sims.shape[0], n)):
#             sims[i : i + n].to_sql(  # noqa
#                 f"{db.RECOMMENDATIONS_BUCKET}_new",
#                 con=conn,
#                 index=False,
#                 if_exists="append",
#                 dtype=db.RECOMMENDATIONS_COLUMNS_SQL,
#                 method="multi",
#             )
#         create_indexes(
#             f"{db.RECOMMENDATIONS_BUCKET}_new", ["source", "target", "distance"]
#         )
#         promote_table(db.RECOMMENDATIONS_BUCKET)
#     t.close_shelve()


# @app.task(bind=True)
# def track_distance(
#     src_id,
#     tgt_id,
#     spectrogram_type="mel",
#     distance_type="euclidean",
#     model="2019-11-25-01_26_chunk-2_epochs-100_name-CNN_SpectrogramV2_",
#     session=None,
#     src_spec=None,
#     tgt_spec=None,
#     src_feats=None,
#     tgt_feats=None,
# ):
#     close_session = False
#     if session is None:
#         session = db.Session()
#         close_session = True

#     # Load a model if a model object was not passed to track_distance function.
#     assert model is not None, "Model can't be None, must pass str or model object!"
#     if isinstance(model, str):
#         model = SpectrogramSimilarity.load(f"/app/models/{model}.tar")

#     # Check if src,tgt, dist is in the tracks_distances table already.
#     distance = session.query(db.TrackDistance).get(
#         {
#             "source_id": src_id,
#             "target_id": tgt_id,
#             "model_id": model.model_id,
#             "distance_type": distance_type,
#         }
#     )
#     if distance:
#         # End function b/c distance is already in the tracks_distances table.
#         return distance.__dict__

#     # If the distance is not in the tracks_distances table we need to
#     # 1) get the spectrograms for both tracks,
#     # 2) get the model embedding for both tracks,
#     # 3) calculate the distance between the two tracks, and
#     # 4) push the distance to the tracks_distances table.
#     # Get src, tgt spectrograms.
#     if (src_spec is None or tgt_spec is None) and (
#         src_feats is None or tgt_feats is None
#     ):
#         try:
#             if src_spec is None and src_feats is None:
#                 src_spec = session.query(db.Spectrogram).get(
#                     {"track_id": src_id, "spectrogram_type": spectrogram_type}
#                 )
#                 src_spec = np.load(BytesIO(src_spec.spectrogram))
#             if tgt_spec is None and tgt_feats is None:
#                 tgt_spec = session.query(db.Spectrogram).get(
#                     {"track_id": tgt_id, "spectrogram_type": spectrogram_type}
#                 )
#                 tgt_spec = np.load(BytesIO(tgt_spec.spectrogram))
#         except Exception as e:
#             raise (e)

#     # Get the model embeddings for both tracks.
#     if src_feats is None or tgt_feats is None:
#         if src_feats is None:
#             src_feats = model.get_features(src_spec)
#         if tgt_feats is None:
#             tgt_feats = model.get_features(tgt_spec)

#     # Calculate the distance between the two tracks.
#     assert (
#         src_feats is not None and tgt_feats is not None
#     ), f"src, tgt features can't be none! ({type(src_feats)}, {type(tgt_feats)})"
#     src_tgt_dist = model.calculate_distance(
#         src_feats, tgt_feats, distance_type=distance_type
#     )

#     # Create a TrackDistance object to add to the tracks_distances table.
#     distance = db.TrackDistance(
#         source_id=src_id,
#         target_id=tgt_id,
#         model_id=model.model_id,
#         distance_type=distance_type,
#         distance=src_tgt_dist,
#     )
#     if close_session:
#         # Push to the tracks_distances table.
#         session.add(distance)
#         db.session_handler(session)
#         session.close()
#     # logger.info(f"src_tgt distance = {src_tgt_dist}")
#     return distance.__dict__


# # @app.task(bind=True)
# def tracks_distances(
#     track_ids,
#     spectrogram_type="mel",
#     distance_type="euclidean",
#     model="2019-11-25-01_26_chunk-2_epochs-100_name-CNN_SpectrogramV2_",
# ):
#     session = db.Session()
#     if isinstance(model, str):
#         model = SpectrogramSimilarity.load(f"/app/models/{model}.tar")

#     # Flatten the track_ids list if it contains pairs (tuples). We will create
#     # pairs later but we need the list to be flat to grab the spectrograms efficiently.
#     flat_track_ids = []
#     if isinstance(track_ids[0], tuple) or isinstance(track_ids[0], list):
#         for pair in track_ids:
#             flat_track_ids.extend(pair)
#         track_ids = flat_track_ids

#     # Grab spectrograms for the track_ids
#     sql_spectrograms = (
#         session.query(db.Spectrogram)
#         .filter(
#             db.Spectrogram.track_id.in_(track_ids),
#             db.Spectrogram.spectrogram_type == spectrogram_type,
#         )
#         .order_by(db.Spectrogram.track_id)
#     )

#     spectrograms = {}
#     for spec in sql_spectrograms:
#         try:
#             spectrograms[spec.track_id] = np.load(BytesIO(spec.spectrogram))
#         except Exception as e:
#             logger.warning(f"Corrupted spectrogram ({spec.track_id}), {e}")

#     # Get the hidden embeddings for each track
#     embeddings = {tid: model.get_features(spec) for tid, spec in spectrograms.items()}

#     # Generate unordered pairs, i.e., [(t1, t2), (t1, t3), (t2, t3)]
#     trackId_pairs = [
#         (x, y) for x in embeddings.keys() for y in embeddings.keys() if y > x
#     ]

#     # Calculate track distances.
#     distances = []
#     for src_id, tgt_id in trackId_pairs:
#         if (
#             session.query(db.TrackDistance).get(
#                 {
#                     "source_id": src_id,
#                     "target_id": tgt_id,
#                     "model_id": model.model_id,
#                     "distance_type": distance_type,
#                 }
#             )
#             is None
#         ):
#             src_tgt_dist = model.calculate_distance(
#                 embeddings[src_id], embeddings[tgt_id], distance_type=distance_type
#             )
#             distances.append(
#                 dict(
#                     source_id=src_id,
#                     target_id=tgt_id,
#                     model_id=model.model_id,
#                     distance_type=distance_type,
#                     distance=src_tgt_dist.item(),
#                 )
#             )
#     # Push distances to the tracks_distances table.
#     distances_calculated = None
#     if len(distances) > 0:
#         try:
#             session.bulk_insert_mappings(db.TrackDistance, distances)
#             db.session_handler(session)
#             distances_calculated = len(distances)
#         except Exception as dup_e:
#             # Tried to add duplicate item(s), this was probably caused b/c another
#             # one of these task executed around the same time and completed before
#             # this one.
#             logger.warning(f"Bulk Insert Error: {dup_e}")
#     session.close()
#     return distances_calculated


# # @app.task(bind=True)
# def test_track_distance():
#     # Upload spectrograms for two tracks to spectrograms table.
#     # Call track_distance
#     session = db.Session()
#     spectrogram_type = "mel"
#     distance_type = "euclidean"
#     model = "2019-11-25-01_26_chunk-2_epochs-100_name-CNN_SpectrogramV2_"
#     model = SpectrogramSimilarity.load(f"/app/models/{model}.tar")
#     # source track: Tame Impala, The Less I Know The Better
#     src_id = "6K4t31amVTZDgR3sKmwUJJ"
#     # target track: MGMT, Denzel Curry, Tokyo Drifting
#     tgt_id = "3Sj4lCOlYVeHpkvuc9W5Vn"

#     # Download and upload spectrogram for source track.
#     res1 = download_spectrogram(
#         src_id, spectrogram_type=spectrogram_type, session=session
#     )
#     # Download and upload spectrogram for target track.
#     res2 = download_spectrogram(
#         tgt_id, spectrogram_type=spectrogram_type, session=session
#     )
#     logger.info(f"src, tgt download response: ({res1}, {res2})")

#     # Calculate distance between the two tracks and push result to the
#     # tracks_distances table.
#     distance = track_distance(
#         src_id=src_id,
#         tgt_id=tgt_id,
#         distance_type=distance_type,
#         model=model,
#         session=session,
#     )
#     msg = f"Distance ({src_id} <> {tgt_id}) = {distance.distance}"
#     logger.info(msg)
#     return msg


# # @app.task(bind=True)
# def test_tracks_distances():
#     model = "2019-11-25-01_26_chunk-2_epochs-100_name-CNN_SpectrogramV2_"
#     model = SpectrogramSimilarity.load(f"/app/models/{model}.tar")

#     query = """
#         select track_id from spectrograms
#         except
#         select source_id from tracks_distances
#         order by track_id
#         limit 20;
#     """
#     with db.engine.connect() as conn:
#         track_ids = pd.read_sql(query, con=conn)["track_id"].to_list()

#     num_distances_calculated = tracks_distances(
#         track_ids=track_ids,
#         spectrogram_type="mel",
#         distance_type="euclidean",
#         model=model,
#     )
#     logger.info(
#         f"Tested tracks_distances! Number of distances calculated = {num_distances_calculated}"
#     )


# # TODO: deprecated, remove.
# # @app.task(bind=True)
# def user_similarity(user_id="krmiddlebrook", n=100, m=100):
#     fin_tracks = None
#     t = SpectrogramSimilarity.load(
#         "/app/models/2019-11-25-01_26_chunk-2_epochs-100_name-CNN_SpectrogramV2_.tar"
#     )
#     t.open_shelve(shelve_path)
#     t.init_shelve()
#     klist = list(t.shelve.keys())
#     print("Starting Query...")
#     with cf.engine.connect() as conn:
#         query = f"""
#                 SELECT track_id
#                        -- , spectrogram
#                 from (
#                     select distinct track_id
#                     from user_tracks ut
#                     left join spectrograms sp
#                     using (track_id)
#                     where sp.track_id is not null
#                         and ut.user_id = '{user_id}'
#                     limit {n}
#                 ) n
#                 join spectrograms k
#                 using (track_id)
#             """
#         source_ids = set(pd.read_sql(query, conn)["track_id"].values)
#         query = f"""
#                 SELECT track_id
#                        -- , spectrogram
#                 from (
#                     SELECT track_id
#                     FROM model_results
#                     group by track_id
#                     having max(probability) > 0.3 and max(playcount) < 500000
#                     order by max(probability) desc, max(playcount/probability) desc
#                 ) n
#                 join spectrograms k
#                 using (track_id)
#                 limit {m}
#             """
#         target_ids = set(pd.read_sql(query, conn)["track_id"].values)
#         to_get = (source_ids | target_ids) - set(klist)
#         for track_id in tqdm(to_get):
#             r = conn.execute(
#                 f"""
#                 SELECT track_id
#                        , spectrogram
#                 from spectrograms k
#                 where track_id = '{track_id}'
#                 limit 1
#                 """
#             )
#             row = r.fetchone()
#             with BytesIO(row[1].tobytes()) as f:
#                 res = np.load(f)
#                 # Precomputing features instead of spectrogram saves time
#                 t.shelve[row[0]] = t.get_features(res)
#                 klist.append(row[0])
#     print("fetch finished, similarity...")
#     sims = []
#     with tqdm(total=len(source_ids) * len(target_ids)) as tq:
#         for tid1 in source_ids:
#             for tid2 in target_ids:
#                 tq.update(1)
#                 if tid1 != tid2:
#                     n = float(t.calculate_distance(tid1, tid2))
#                     sims.append((tid1, tid2, n))
#     print("sim_finished!")
#     sims = pd.DataFrame(sims, columns=("source", "target", "distance"))
#     end_tracks = sims.groupby(["target"]).sum().sort_values("distance")
#     fin_tracks = list(end_tracks.index)
#     t.close_shelve()
#     return fin_tracks


# # @app.task(bind=True)
# def generate_playlist(
#     user_id, track_ids, n=5, conn_timeout=3, read_timeout=10, sleep_time=0.4
# ):
#     sp = SpotifyMux(0)
#     now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")  # current date and time
#     tracks = [f"spotify:track:{tid}" for tid in track_ids[:n]]
#     token = sp.token(user_id)
#     my_id = requests.get(
#         "https://api.spotify.com/v1/me",  # noqa: E501
#         headers={"Authorization": f"Bearer {token}"},
#         params={
#             "market": "from_token",
#             "platform": "desktop",
#             "catalogue": "premium",
#             "format": "json",
#         },
#         timeout=(conn_timeout, read_timeout),
#     ).json()["id"]
#     resp = requests.post(
#         f"https://api.spotify.com/v1/users/{my_id}/playlists",  # noqa: E501
#         headers={
#             "Authorization": f"Bearer {token}",
#             "Content-Type": "application/json",
#         },
#         json=dict(
#             name=f"Hip musicai.io playlist for {user_id}! {now}",
#             description=f"A playlist created just for you of emerging tracks! Enjoy :), the team @ musicai.io",
#         ),
#         timeout=(conn_timeout, read_timeout),
#     ).json()
#     playlist_id = resp["id"]
#     url = resp["external_urls"]["spotify"]
#     requests.post(
#         f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",  # noqa: E501
#         headers={
#             "Authorization": f"Bearer {token}",
#             "Content-Type": "application/json",
#         },
#         json=dict(uris=tracks,),
#         timeout=(conn_timeout, read_timeout),
#     )
#     return url
