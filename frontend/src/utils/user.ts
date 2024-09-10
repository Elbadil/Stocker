import { api } from '../api/axios';

export const fetchUserData = async (userId: string | undefined) => {
  if (!userId) {
    throw new Error('userId not provided');
  }
  try {
    const res = await api.get(`/users/${userId}/`);
    return res.data;
  } catch (err) {
    throw err;
  }
};
