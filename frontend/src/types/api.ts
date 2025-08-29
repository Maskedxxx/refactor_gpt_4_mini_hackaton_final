// TypeScript types based on backend Pydantic models

// Resume Models (from src/models/resume_models.py)
export interface Level {
  name: string;
}

export interface RelocationType {
  name: string;
}

export interface Certificate {
  title: string;
  url?: string;
}

export interface ContactValue {
  formatted: string;
}

export interface ContactType {
  name: string;
}

export interface Contact {
  type: ContactType;
  value: string | ContactValue;
}

export interface SiteType {
  name: string;
}

export interface Site {
  type: SiteType;
  url: string;
}

export interface Experience {
  description: string;
  position: string;
  company?: string;
  start?: string;
  end?: string;
}

export interface Language {
  name: string;
  level: Level;
}

export interface Relocation {
  type: RelocationType;
}

export interface Salary {
  amount: number;
}

export interface ProfessionalRole {
  name: string;
}

export interface EducationLevel {
  name: string;
}

export interface PrimaryEducation {
  name: string;
  organization?: string;
  result?: string;
  year?: number;
}

export interface AdditionalEducation {
  name: string;
  organization?: string;
  result?: string;
  year?: number;
}

export interface Education {
  level?: EducationLevel;
  primary: PrimaryEducation[];
  additional: AdditionalEducation[];
}

export interface ResumeInfo {
  first_name?: string;
  last_name?: string;
  middle_name?: string;
  title: string;
  total_experience?: number;
  skills: string;
  skill_set: string[];
  experience: Experience[];
  employments: string[];
  schedules: string[];
  languages: Language[];
  relocation?: Relocation;
  salary?: Salary;
  professional_roles: ProfessionalRole[];
  education?: Education;
  certificate: Certificate[];
  contact: Contact[];
  site: Site[];
}

// Vacancy Models (from src/models/vacancy_models.py)
export interface EmploymentForm {
  id: string;
}

export interface ExperienceVac {
  id: string;
}

export interface Schedule {
  id: string;
}

export interface Employment {
  id: string;
}

export interface VacancyProfessionalRole {
  name: string;
}

export interface VacancyInfo {
  name: string;
  company_name: string;
  description: string;
  key_skills: string[];
  professional_roles: VacancyProfessionalRole[];
  employment_form?: EmploymentForm;
  experience?: ExperienceVac;
  schedule?: Schedule;
  employment?: Employment;
}

// Session API (from src/webapp/sessions.py)
export interface SessionInitResponse {
  session_id: string;
  resume_id: string;
  vacancy_id: string;
  resume: ResumeInfo;
  vacancy: VacancyInfo;
  reused: {
    resume: boolean;
    vacancy: boolean;
  };
}

// Features API (from src/webapp/features.py)
export interface FeatureListResponse {
  features: Record<string, {
    description: string;
    versions: string[];
    default_version: string;
  }>;
}