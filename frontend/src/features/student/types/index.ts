export type Proficiency = 'Beginner' | 'Intermediate' | 'Advanced';

export type SkillCategory =
  | 'Programming Languages'
  | 'Frontend'
  | 'Backend'
  | 'Database'
  | 'Cloud'
  | 'AI / ML'
  | 'Tools';

export type Skill = {
  id: string;
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
