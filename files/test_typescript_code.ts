interface User {
  id: string;
  name: string;
  email: string;
  age?: number;
}

type Status = 'active' | 'inactive' | 'pending';

enum Role {
  Admin = 'ADMIN',
  User = 'USER',
  Guest = 'GUEST'
}

class UserService {
  async getUser(id: string): Promise<User> {
    // Implementation
    return {} as User;
  }
}