import axios, { AxiosError } from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 10_000,
});

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const detail = error.response?.data?.detail ?? error.message;
    return Promise.reject(new Error(detail));
  },
);

export default client;
