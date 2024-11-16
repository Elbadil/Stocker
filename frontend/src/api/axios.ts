import axios from 'axios';
import { clearUser, setUser } from '../store/slices/authSlice';
import { store } from '../store/store';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

api.interceptors.request.use(async function (config) {
  console.log('Interceptor working.. URL:', config.url);
  const requireAuthPaths = [
    '/auth/user/',
    '/auth/logout/',
    '/auth/user/change-password/',
  ];
  if (
    config.url &&
    config.url.startsWith('/auth') &&
    !requireAuthPaths.includes(config.url)
  ) {
    return config;
  }
  const state = store.getState();
  const accessToken = state.auth.accessToken;
  if (accessToken) {
    try {
      await api.post('/auth/token/verify/', {
        token: accessToken,
      });
      config.headers.Authorization = `Bearer ${accessToken}`;
      return config;
    } catch (err) {
      console.log('Error verifying the access token:', err);
    }
  }
  try {
    const res = await api.post('/auth/token/refresh/');
    const newAccessToken = res.data.access_token;
    store.dispatch(setUser(res.data));
    config.headers.Authorization = `Bearer ${newAccessToken}`;
  } catch (err) {
    console.log('Error refreshing the access token:', err);
    store.dispatch(clearUser());
    return Promise.reject(err);
  }
  return config;
});
