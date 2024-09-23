import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { api } from '../../api/axios';
import { RootState } from '../store';

export interface UserProps {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  avatar: string | null;
  bio: string;
}

export interface AuthState {
  accessToken: string | null;
  user: UserProps | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | Array<string> | null;
}

export interface UserAndToken {
  user: UserProps;
  access_token: string;
}

const initialState: AuthState = {
  accessToken: null,
  user: null,
  isAuthenticated: false,
  loading: true,
  error: null,
};

export const validateTokenAndSetUserAsync = createAsyncThunk<
  UserAndToken,
  void,
  { state: RootState }
>('auth/validateTokenAndSetUserAsync', async (_, { getState }) => {
  const state = getState();
  const accessToken = state.auth.accessToken;
  const user = state.auth.user;
  if (accessToken && user) {
    const tokenClaims = JSON.parse(atob(accessToken.split('.')[1]));
    const tokenExpiryDate = new Date(tokenClaims.exp * 1000);
    const dateNow = new Date();
    if (tokenExpiryDate >= dateNow) {
      return { user, access_token: accessToken };
    }
  }
  try {
    const res = await api.post('/auth/token/refresh/');
    return res.data;
  } catch (err: any) {
    console.log('Error refreshing access token:', err);
    throw new Error(err.response?.data?.errors || 'Token validation failed');
  }
});

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action) => {
      if (action.payload.user) {
        state.user = action.payload.user;
      }
      if (action.payload.access_token) {
        state.accessToken = action.payload.access_token;
      }
      state.isAuthenticated = true;
    },
    clearUser: (state) => {
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(validateTokenAndSetUserAsync.pending, (state) => {
        state.loading = true;
      })
      .addCase(validateTokenAndSetUserAsync.fulfilled, (state, action) => {
        state.accessToken = action.payload.access_token;
        state.user = action.payload.user;
        state.loading = false;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(validateTokenAndSetUserAsync.rejected, (state, action) => {
        state.accessToken = null;
        state.user = null;
        state.isAuthenticated = false;
        state.loading = false;
        state.error =
          action.error.message || 'Failed to get/refresh the access token.';
      });
  },
});

export const { setUser, clearUser } = authSlice.actions;
export default authSlice.reducer;
