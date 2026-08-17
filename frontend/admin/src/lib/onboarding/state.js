export const state = {
    step: 0,
    account: { email: "", username: "", password: "" },
    clinic: { name: "", slug: "", email: "", phone_number: "", address: "" },
    services: [],
    slugTouched: false,
    token: null,
    createdClinic: null,
    createdServices: [],
    apiKey: null,
};

let serviceSeq = 0;
export function newService() {
    serviceSeq += 1;
    return { _id: serviceSeq, name: "", category: "wellness_exam", customCategory: "", price: "", duration_minutes: "", description: "" };
}

state.services.push(newService());