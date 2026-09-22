export function retainedFieldStatus(field) {
  const status = field?.status;
  return status === "provisional" || status === "conflict" || status === "verified"
    ? status
    : "verified";
}
