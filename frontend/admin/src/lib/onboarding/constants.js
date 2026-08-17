// Matches the categories the backend actually recognizes
export const SUGGESTED_CATEGORIES = [
    "wellness_exam", "vaccination", "microchipping", "nail_trim", "bloodwork",
    "imaging", "lab_testing", "sick_visit", "dental_cleaning", "spay_neuter",
    "surgery", "wound_care", "grooming", "boarding", "end_of_life",
];

export const CATEGORY_LABELS = {
    wellness_exam: "Wellness exam", vaccination: "Vaccination", microchipping: "Microchipping",
    nail_trim: "Nail trim", bloodwork: "Bloodwork", imaging: "Imaging", lab_testing: "Lab testing",
    sick_visit: "Sick visit", dental_cleaning: "Dental cleaning", spay_neuter: "Spay / neuter",
    surgery: "Surgery", wound_care: "Wound care", grooming: "Grooming", boarding: "Boarding",
    end_of_life: "End of life",
};

export const STEP_LABELS = ["Account", "Clinic", "Services", "Review"];

export const TASKS = [
    { key: "account", label: "Creating your account" },
    { key: "clinic", label: "Setting up the clinic" },
    { key: "services", label: "Adding services" },
    { key: "key", label: "Issuing a public booking key" },
];