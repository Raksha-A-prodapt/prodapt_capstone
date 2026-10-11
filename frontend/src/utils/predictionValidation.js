export function validatePredictionInputs(inputs, features, required) {
  const errors = [];

  for (const [key, , unit, type] of features) {
    const value = inputs[key];
    const empty = value === '' || value === null || value === undefined;

    if (required.has(key) && empty) {
      errors.push(`${key} is required.`);
      continue;
    }
    if (empty || type !== 'number') continue;

    const number = Number(value);
    if (!Number.isFinite(number)) {
      errors.push(`${key} must be a finite number.`);
    } else if (unit === '%' && (number < 0 || number > 100)) {
      errors.push(`${key} must be between 0 and 100.`);
    } else if (['total', 'users', 'GB', 'hours'].includes(unit) && number < 0) {
      errors.push(`${key} cannot be negative.`);
    }
  }

  return errors;
}
