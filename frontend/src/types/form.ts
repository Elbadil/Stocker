export type FormValues = {
  [key: string]: string;
}

export type FormErrors = {
  [key: string]: string | Array<string>;
}

export type SelectOption = {
  value: string;
  label: string;
}