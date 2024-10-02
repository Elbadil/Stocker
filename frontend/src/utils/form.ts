import React from 'react';
import { z } from 'zod';
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

export const resetFormValues = (
  formValues: FormValues,
  setFormValues: React.Dispatch<React.SetStateAction<FormValues>>,
) => {
  const resetValues: FormValues = {};
  for (const key in formValues) {
    resetValues[key] = '';
  }
  setFormValues({
    ...resetValues,
  });
};

export const areFieldsFilled = (fields: FormValues) => {
  return Object.values(fields).every((value) => value.trim() !== '');
};

export const minLengthWithMessage = (minValue: number, fieldName: string) =>
  z
    .string()
    .min(minValue, `${fieldName} must be at least ${minValue} characters long`);

export const requiredStringField = (fieldName: string) =>
  z.string().min(1, `${fieldName} is required.`);

export const nonBlankField = (fieldName: string) =>
  z.string().min(1, `${fieldName} can't be blank.`);

export const requiredPositiveNumberField = (fieldName: string) => {
  return z
    .union([z.string(), z.number()]) // Accepting either a string (before coercion) or a number
    .refine(
      (value) => {
        if (typeof value === 'string' && value.trim() === '') return false; // Catch empty string input
        return !isNaN(Number(value)); // Checking if it can be coerced to a valid number (handle NaN)
      },
      { message: `${fieldName} is required` },
    ) // Displaying "Price is required" when input is empty or invalid
    .transform((value) => Number(value)) // Coercing the value to a number after the required check
    .refine((value) => value > 0, {
      message: `${fieldName} must be a positive number`,
    }); // Ensuring it's positive
};

export const fileField = () => {
  return z
    .instanceof(FileList)
    .optional()
    .refine(
      (files) => {
        if (!files || files.length === 0) return true; // Allow no file if optional
        const file = files[0];
        return ['image/jpeg', 'image/png'].includes(file.type); // Check file type
      },
      { message: 'Only JPEG or PNG files are allowed' },
    )
    .refine(
      (files) => {
        if (!files || files.length === 0) return true; // Allow no file if optional
        const file = files[0];
        return file.size <= 2000000; // 2MB // Limit file size
      },
      { message: 'Picture size must be less than or equal to 2MB' },
    );
};
