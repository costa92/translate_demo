import axios from "axios";

// 创建 axios 实例
const api = axios.create({
  baseURL: "http://localhost:8001", // 使用8001端口，与后端一致
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证令牌等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    // 处理错误响应
    const errorMessage = error.response?.data?.message || "发生未知错误";
    console.error("API 错误:", errorMessage);
    return Promise.reject(error);
  }
);

export default api;
