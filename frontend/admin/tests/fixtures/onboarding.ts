/**
 * Static input data for the onboarding wizard tests. Centralized here so new
 * onboarding specs can reuse the same account/clinic/service data instead of
 * re-declaring it inline — see tests/onboarding.spec.ts for the flow this feeds.
 */

export const account = {
  email: 'jane@acmevet.com',
  username: 'janedoe_vet',
  password: 'supersecret1',
};

// Deliberately different from `account.password`, for the "confirm password
// doesn't match" validation case.
export const mismatchedConfirmPassword = 'somethingElse';

export const clinic = {
  name: 'Acme Veterinary Clinic',
  // Expected auto-derived value of #cl_slug once `clinic.name` is typed in.
  slug: 'acme-veterinary-clinic',
  email: 'hello@acmevet.com',
  phone: '+52 55 0000 0000',
  address: '123 Main St, CDMX',
};

export const service = {
  name: 'Annual wellness exam',
  price: '450',
  duration: '30',
};
