import React from 'react';
import { z } from 'zod';
import { CSSObject } from '@emotion/react';
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

export const areFieldsEmpty = (object: { [key: string]: string | number }) =>
  Object.values(object).every(
    (value) =>
      value === null ||
      value === undefined ||
      (typeof value === 'string' && value.trim() === '') ||
      value === '',
  );

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

export const optionalEmailField = () =>
  z.preprocess(
    (val) => (val === '' ? null : val),
    z.string().email().optional().nullable(),
  );

export const optionalStringField = () =>
  z.preprocess(
    (val) => (val === '' ? null : val),
    z.string().optional().nullable(),
  );

export const optionalNumberField = () =>
  z.preprocess(
    (val) => (val ? Number(val) : null),
    z.number().optional().nullable(),
  );

export const locationField = () =>
  z
    .object({
      country: z.string().optional().nullable(),
      city: z.string().optional().nullable(),
      street_address: z.preprocess(
        (val) => (val === '' ? undefined : val),
        z.string().optional().nullable(),
      ),
    })
    .transform((loc) => {
      // If all properties are null or undefined, return undefined
      return Object.values(loc).every(
        (val) => val === null || val === undefined,
      )
        ? null
        : loc;
    });

export const orderedItemsField = () =>
  z
    .array(
      z.object({
        item: requiredStringField('Item name'),
        ordered_quantity: requiredPositiveNumberField('Quantity'),
        ordered_price: requiredPositiveNumberField('Price'),
      }),
    )
    .superRefine((orderedItems, ctx) => {
      // Collect all items names
      const itemNames = orderedItems.map((orderedItem) => orderedItem.item);
      const nameCount: { [key: string]: number } = {};
      itemNames.forEach((name: string, index: number) => {
        const nameLower = name.toLowerCase().trim();
        nameCount[nameLower] = (nameCount[nameLower] || 0) + 1;
        if (nameCount[nameLower] > 1) {
          ctx.addIssue({
            code: 'custom',
            path: [index, 'item'], // Point to the specific field in the array
            message: `Item "${name.trim()}" has already been selected.`,
          });
        }
      });
    });

export const selectOptionsFromStrings = (options: string[]) =>
  options.map((option) => ({ value: option, label: option }));

export const selectOptionsFromObjects = (
  options: { name: string; [key: string]: any }[],
) => options.map((option) => ({ value: option.name, label: option.name }));

export const statusType = (status: string) => {
  const completedStatus = ['Paid', 'Delivered'];
  const activeStatus = ['Pending', 'Shipped'];
  if (completedStatus.includes(status)) {
    return 'completed';
  } else if (activeStatus.includes(status)) {
    return 'active';
  }
  return 'failed';
};


export const customSelectStyles = (isDarkMode: boolean) => ({
  control: (provided: CSSObject, state: any) => ({
    ...provided,
    backgroundColor: isDarkMode ? '#313d4a' : '#eff4fb', // Background changes based on mode
    padding: '0.12rem 0.3rem',
    borderColor: state.isFocused
      ? '#3c50e0'
      : isDarkMode
      ? '#5a6b7f'
      : '#e2e8f0', // Border changes on focus or mode
    boxShadow: state.isFocused ? '0 0 0 1px #3c50e0' : 'none', // Add focus styling
    '&:hover': {
      borderColor: state.isFocused
        ? '#3c50e0'
        : isDarkMode
        ? '#5a6b7f'
        : '#2e3a47', // Hover state
    },
  }),
  menu: (provided: CSSObject) => ({
    ...provided,
    backgroundColor: isDarkMode ? '#313d4a' : '#ffffff', // Dark mode for menu background
    color: isDarkMode ? '#ffffff' : '#000000',
  }),
  singleValue: (provided: CSSObject) => ({
    ...provided,
    color: isDarkMode ? '#ffffff' : '#000000', // Text color based on mode
  }),
  option: (provided: CSSObject, state: any) => ({
    ...provided,
    backgroundColor: state.isSelected
      ? isDarkMode
        ? '#3c50e0'
        : '#eff4fb' // Highlight selected option
      : state.isFocused
      ? isDarkMode
        ? '#425b70'
        : '#ebf2fa'
      : 'transparent',
    color: isDarkMode ? '#ffffff' : '#000000',
    '&:hover': {
      backgroundColor: isDarkMode ? '#425b70' : '#ebf2fa', // Hover state
    },
  }),
  placeholder: (provided: CSSObject) => ({
    ...provided,
    color: isDarkMode ? 'rgb(148 163 184)' : 'rgb(148 163 184)', // Placeholder color based on mode
  }),
  input: (provided: CSSObject) => ({
    ...provided,
    color: isDarkMode ? '#ffffff' : '#000000', // Text color for typed input
  }),
  menuList: (provided: CSSObject) => ({
    ...provided,
    maxHeight: 150, // Set maximum height for the dropdown (in pixels)
  }),
});
