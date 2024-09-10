import React from 'react';
import { FormErrors, FormValues } from '../types/form';

export const handleInputChange = (
  e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  formValues: FormValues,
  setFormValues: React.Dispatch<React.SetStateAction<FormValues>>,
) => {
  const { name, value } = e.target;
  setFormValues({
    ...formValues,
    [name]: value,
  });
};

export const handleInputErrors = (
  formErrors: FormErrors,
  setFormErrors: React.Dispatch<React.SetStateAction<FormErrors>>,
) => {
  const resetErrors: FormErrors = {};
  for (const key in formErrors) {
    resetErrors[key] = '';
  }
  setFormErrors({
    ...resetErrors,
    ...formErrors,
  });
};

export const removeBlankFields = (formValues: FormValues) => {
  const cleanedValues: FormValues = {};
  for (const key in formValues) {
    if (formValues[key].trim() !== '') {
      cleanedValues[key] = formValues[key];
    }
  }
  return cleanedValues;
};

export const resetFormErrors = (
  formErrors: FormErrors,
  setFormErrors: React.Dispatch<React.SetStateAction<FormErrors>>,
) => {
  const resetErrors: FormErrors = {};
  for (const key in formErrors) {
    resetErrors[key] = '';
  }
  setFormErrors({
    ...resetErrors,
  });
};
