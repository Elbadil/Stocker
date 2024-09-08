import api from '../api/axios';

export const getAccessToken = () => localStorage.getItem('access_token');
export const setAccessToken = (token: string) =>
  localStorage.setItem('access_token', token);

export const getRefreshToken = () => localStorage.getItem('refresh_token');

export const setTokens = (tokens: { [key: string]: string }) => {
  localStorage.setItem('access_token', tokens.access);
  localStorage.setItem('refresh_token', tokens.refresh);
};

export const removeTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  try {
    const res = await api.post('/auth/token/refresh/', {
      refresh: refreshToken,
    });
    const newAccessToken = res.data.access;
    setAccessToken(newAccessToken);
    return newAccessToken;
  } catch (err) {
    throw err;
  }
};

export const logoutUser = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  try {
    const res = await api.post('/auth/logout/', {
      refresh: refreshToken,
    });
    const { message } = res.data;
    console.log(message);
  } catch (err) {
    console.log('Error Logging the user out', err);
  } finally {
    removeTokens();
    window.location.href = '/auth/signin';
  }
};
