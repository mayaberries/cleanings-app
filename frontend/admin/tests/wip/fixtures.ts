/**
 * Placeholder input data for the roadmap specs in tests/wip/. Shapes follow
 * the request/response schemas in docs/openapi.json (ServiceCreate,
 * AppointmentPublic, ClinicAPIKeyCreate, ClinicUpdate, ...). See
 * tests/wip/README.md before editing — this file gets pared down as specs
 * graduate out of wip/.
 */

// ServiceCreate — POST /api/services/
export const newService = {
  name: 'Dental Cleaning',
  category: 'dental_cleaning',
  price: '120',
  duration_minutes: '45',
  description: 'Full dental cleaning under anesthesia.',
};

// AppointmentPublic (subset) — GET /api/services/{service_id}/appointments/
export const existingAppointment = {
  petName: 'Biscuit',
  clientName: 'Jordan Lee',
  serviceName: 'Wellness Exam',
  status: 'requested',
};

// ClinicAPIKeyCreate — POST /api/clinics/{clinic_id}/api-keys/
export const newApiKey = {
  label: 'Website widget',
  environment: 'live',
};

// ClinicUpdate — PUT /api/clinics/{clinic_id}/
export const clinicProfileUpdate = {
  address: '456 Renewed Ave, CDMX',
};

// ClinicAvailabilityUpdate — PUT /api/clinics/{clinic_id}/availability/
export const mondayHours = {
  start: '09:00',
  end: '17:00',
};
