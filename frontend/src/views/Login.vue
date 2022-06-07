<template>
  <!-- <v-row cols="12" lg="12" md="12" sm="12"> -->
  <v-container fluid>
    <v-row dense cols="12" justify="center">
      <v-card class="elevation-12">
        <v-toolbar dark color="primary">
          <v-toolbar-title>{{ appName }}</v-toolbar-title>
          <v-spacer></v-spacer>
        </v-toolbar>

        <v-card-text>
          <v-form @keyup.enter="submit">
            <v-text-field
              @keyup.enter="submit"
              v-model="email"
              prepend-icon="person"
              name="login"
              label="Login"
              type="text"
            ></v-text-field>
            <v-text-field
              @keyup.enter="submit"
              v-model="password"
              prepend-icon="lock"
              name="password"
              label="Password"
              id="password"
              type="password"
            ></v-text-field>
          </v-form>

          <div v-if="loginError">
            <v-alert
              :value="loginError"
              transition="fade-transition"
              type="error"
            >
              Incorrect email or password
            </v-alert>
          </div>

          <div class="caption text-xs-right">
            <router-link to="/recover-password"
              >Forgot your password?</router-link
            >
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn to="/main/profile/create">Create Account</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click.prevent="submit">Login</v-btn>
        </v-card-actions>
      </v-card>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { api } from '@/api';
import { appName } from '@/env';
import { readLoginError } from '@/store/main/getters';
import { dispatchLogIn } from '@/store/main/actions';

@Component
export default class Login extends Vue {
  public email: string = '';
  public password: string = '';
  public appName = appName;

  public get loginError() {
    return readLoginError(this.$store);
  }

  public submit() {
    dispatchLogIn(this.$store, {
      username: this.email,
      password: this.password,
    });
  }
}
</script>

<style></style>
