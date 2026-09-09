import type { ProfileData, Skill, ResumeVersion } from '../types';

export const profileData: ProfileData = {
  fullName: 'Aarav Sharma',
  email: 'aarav.sharma@university.edu',
  phone: '+91 98765 43210',
  department: 'Computer Science & Engineering',
  graduationYear: '2027',
  cgpa: '8.7',
  dateOfBirth: '2004-03-15',
  address: '123 MG Road, Bengaluru, Karnataka 560001, India',
  linkedin: 'linkedin.com/in/aaravsharma',
  github: 'github.com/aaravsharma',
  avatarText: 'AS',
};

export const initialSkills: Skill[] = [
  { id: 1, name: 'JavaScript', category: 'Programming Languages', proficiency: 'Advanced' },
  { id: 2, name: 'TypeScript', category: 'Programming Languages', proficiency: 'Intermediate' },
  { id: 3, name: 'Python', category: 'Programming Languages', proficiency: 'Advanced' },
  { id: 4, name: 'Java', category: 'Programming Languages', proficiency: 'Intermediate' },
  { id: 5, name: 'React', category: 'Frontend', proficiency: 'Advanced' },
  { id: 6, name: 'CSS / Tailwind', category: 'Frontend', proficiency: 'Advanced' },
  { id: 7, name: 'HTML5', category: 'Frontend', proficiency: 'Advanced' },
  { id: 8, name: 'Node.js', category: 'Backend', proficiency: 'Intermediate' },
  { id: 9, name: 'Express', category: 'Backend', proficiency: 'Intermediate' },
  { id: 10, name: 'REST APIs', category: 'Backend', proficiency: 'Advanced' },
  { id: 11, name: 'PostgreSQL', category: 'Database', proficiency: 'Intermediate' },
  { id: 12, name: 'MongoDB', category: 'Database', proficiency: 'Beginner' },
  { id: 13, name: 'AWS', category: 'Cloud', proficiency: 'Beginner' },
  { id: 14, name: 'Docker', category: 'Cloud', proficiency: 'Beginner' },
  { id: 15, name: 'TensorFlow', category: 'AI / ML', proficiency: 'Beginner' },
  { id: 16, name: 'Scikit-learn', category: 'AI / ML', proficiency: 'Intermediate' },
  { id: 17, name: 'Git', category: 'Tools', proficiency: 'Advanced' },
  { id: 18, name: 'VS Code', category: 'Tools', proficiency: 'Advanced' },
  { id: 19, name: 'Figma', category: 'Tools', proficiency: 'Intermediate' },
  { id: 20, name: 'Jest', category: 'Tools', proficiency: 'Beginner' },
];

export const resumeVersions: ResumeVersion[] = [
  {
    id: 'RES-003',
    fileName: 'Aarav_Sharma_Resume_v3.pdf',
    version: 'v3',
    uploadDate: '2026-08-05',
    fileSize: '248 KB',
    isActive: true,
  },
  {
    id: 'RES-002',
    fileName: 'Aarav_Sharma_Resume_v2.pdf',
    version: 'v2',
    uploadDate: '2026-06-12',
    fileSize: '235 KB',
    isActive: false,
  },
  {
    id: 'RES-001',
    fileName: 'Aarav_Sharma_Resume_v1.pdf',
    version: 'v1',
    uploadDate: '2026-01-20',
    fileSize: '198 KB',
    isActive: false,
  },
];
