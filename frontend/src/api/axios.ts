import axios from 'axios';
import { getAccessToken, refreshAccessToken, logoutUser } from '../utils/auth';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: { 'Content-Type': 'application/json' },
});

export const refreshApi = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(async function (config) {
  console.log('Interceptor working.. URL:', config.url);
  const accessToken = getAccessToken();
  if (accessToken) {
    const userData = JSON.parse(atob(accessToken.split('.')[1]));
    const tokenExpiryDate = new Date(userData.exp * 1000);
    const dateNow = new Date(Date.now());
    if (dateNow >= tokenExpiryDate) {
      try {
        console.log('Attempting to refresh from axios.')
        const newAccessToken = await refreshAccessToken();
        config.headers.Authorization = `Bearer ${newAccessToken}`;
        console.log('refreshed from axios');
      } catch (err) {
        console.log(
          'Axios Interceptor: Error refreshing the access token',
          err,
        );
        console.log('Lets log out the user');
        await logoutUser();
        return Promise.reject(err);
      }
    } else {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
  }

  return config;
});
