export type Proficiency = 'Beginner' | 'Intermediate' | 'Advanced';

export type SkillCategory = string;

export type Skill = {
  id: number;
  name: string;
  category: SkillCategory;
  proficiency: Proficiency;
};

export type ProfileData = {
  fullName: string;
  email: string;
  phone: string;
  department: string;
  graduationYear: string;
  cgpa: string;
  dateOfBirth: string;
  address: string;
  linkedin: string;
  github: string;
  avatarText: string;
};

export type ResumeVersion = {
  id: string;
  fileName: string;
  version: string;
  uploadDate: string;
  fileSize: string;
  isActive: boolean;
};
