// src/api.js
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8080",
  timeout: 10000,
});

export const getBalance = () => api.get("/api/virtual/balance");
export const resetBalance = (amount) => api.post(`/api/virtual/reset`, null, { params: { amount } });
export const deposit = (amount) => api.post(`/api/virtual/deposit`, null, { params: { amount } });

export const getQuote = (symbol) => api.get(`/api/quote/${symbol}`);

export const placeOrder = (body) =>
  api.post("/api/virtual/order", body);

export const getOrders = () => api.get("/api/virtual/orders");
export const getTrades = () => api.get("/api/virtual/trades");

export default api;
