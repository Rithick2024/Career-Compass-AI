import api from '../../../api/axios';
import * as tokenUtils from '../utils/token';

export interface LoginCredentials {
  username: string; // FastAPI OAuth2PasswordRequestForm uses 'username' for email
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<User> {
    // Backend expects a JSON payload matching UserLoginRequest
    const payload = {
      email: credentials.username, // mapping frontend 'username' to backend 'email'
      password: credentials.password,
    };

    const response = await api.post<LoginResponse>('/auth/login', payload);
    
    // Store token
    tokenUtils.setToken(response.data.access_token);
    return response.data.user;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  async register(credentials: LoginCredentials): Promise<void> {
    const payload = {
      email: credentials.username,
      password: credentials.password,
    };
    await api.post('/auth/register', payload);
  },
};
