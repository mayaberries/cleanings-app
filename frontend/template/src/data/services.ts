export interface ServiceItem {
  title: string;
  description: string;
}

// Hardcoded for now. Once services live behind an API, this becomes a
// fetch (or a prop passed down from a loader) instead of a static array —
// ServiceCard / ServicesSection don't need to change either way.
export const services: ServiceItem[] = [
  {
    title: "Wellness exams",
    description: "Annual checkups, weight and diet reviews, senior pet care.",
  },
  {
    title: "Vaccinations",
    description: "Core and lifestyle vaccines, titers, and travel documentation.",
  },
  {
    title: "Dental care",
    description: "Cleanings, extractions, and at-home care plans.",
  },
  {
    title: "Urgent visits",
    description: "Not life-threatening, but can't wait? We hold same-day slots.",
  },
  {
    title: "Grooming",
    description: "Baths, trims, and nail care — solo or paired with an exam.",
  },
];
