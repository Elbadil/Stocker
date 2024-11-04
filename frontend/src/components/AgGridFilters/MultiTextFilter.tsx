import { useGridFilter, CustomFilterProps } from '@ag-grid-community/react';
import {
  IDoesFilterPassParams,
  IAfterGuiAttachedParams,
} from '@ag-grid-community/core';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import { useAlert } from '../../contexts/AlertContext';
import { useRef, useState, useCallback } from 'react';

const MultiTextFilter = ({
  model,
  onModelChange,
  getValue,
}: CustomFilterProps) => {
  const { isDarkMode } = useAlert();
  const inputRef = useRef<HTMLInputElement>(null);
  const hidePopupRef = useRef<(() => void) | null>(null);
  const [filterType, setFilterType] = useState<string>('contains');
  const [filterValue, setFilterValue] = useState<string | null>(null);

  const doesFilterPass = useCallback(
    ({ node }: IDoesFilterPassParams) => {
      const cellValue = getValue(node) || [];
      if (filterValue) {
        const filterTypeLowerCase = filterValue.toLowerCase();
        switch (filterType) {
          case 'contains':
            return cellValue.some((value: string) =>
              value.toLowerCase().includes(filterTypeLowerCase),
            );
          case 'equals':
            return cellValue.some(
              (value: string) => value.toLowerCase() === filterTypeLowerCase,
            );
          case 'doesNotContain':
            return !cellValue.some((value: string) =>
              value.toLowerCase().includes(filterTypeLowerCase),
            );
          case 'beginsWith':
            return cellValue.some((value: string) =>
              value.toLowerCase().startsWith(filterTypeLowerCase),
            );
          case 'endsWith':
            return cellValue.some((value: string) =>
              value.toLowerCase().endsWith(filterTypeLowerCase),
            );
          default:
            return false;
        }
      }
      return false;
    },
    [model, getValue],
  );

  const afterGuiAttached = (params: IAfterGuiAttachedParams) => {
    if (!params.suppressFocus && inputRef.current) {
      inputRef.current.focus();
    }
    if (params.hidePopup) {
      hidePopupRef.current = params.hidePopup;
    }
  };

  useGridFilter({ doesFilterPass, afterGuiAttached });

  const applyFilter = () => {
    onModelChange(filterValue || null);
    if (hidePopupRef.current) hidePopupRef.current();
  };

  const resetFilter = () => {
    setFilterValue('');
    onModelChange(null);
    if (hidePopupRef.current) hidePopupRef.current();
  };

  return (
    <div className="max-w-sm p-2.5 rounded-lg shadow dark:bg-gray-800">
      <div className="w-full custom-filter">
        <div className="relative mb-2">
          <select
            className={`custom-select ${
              isDarkMode ? 'dark' : 'light'
            } w-full p-1 bg-white dark:bg-customDark rounded-md border-2 border-stroke focus:border-blue-400 focus-visible:outline-none dark:focus:border-blue-400 dark:border-strokedark`}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="contains">Contains</option>
            <option value="doesNotContain">Does not contain</option>
            <option value="equals">Equals</option>
            <option value="beginsWith">Begins with</option>
            <option value="endsWith">Ends with</option>
          </select>
        </div>

        <div className="relative mb-2">
          <SearchRoundedIcon
            className="text-slate-400"
            sx={{
              position: 'absolute',
              left: '0.35rem',
              top: '0.6rem',
              fontSize: '16px',
            }}
          />
          <input
            type="text"
            ref={inputRef}
            value={filterValue || ''}
            onChange={(e) => setFilterValue(e.target.value)}
            placeholder={'Filter...'}
            className="w-full py-1.5 pl-5.5 appearance-none bg-white dark:bg-customDark rounded-md border-2 border-stroke focus:border-blue-400 focus-visible:outline-none dark:focus:border-blue-400 dark:border-strokedark no-arrows"
            style={{
              MozAppearance: 'textfield',
              WebkitAppearance: 'none',
            }}
          />
        </div>
      </div>
      <div className="mt-4 mb-1 flex justify-end gap-4">
        <button
          onClick={applyFilter}
          className="py-2.5 px-4 bg-white dark:bg-customDark border border-slate-300 dark:border-slate-600 rounded-md text-center text-black dark:text-white hover:bg-slate-200 dark:hover:bg-sky-900"
        >
          Apply
        </button>
        <button
          onClick={resetFilter}
          className="py-2.5 px-4 bg-white dark:bg-customDark border border-slate-300 dark:border-slate-600 rounded-md text-center text-black dark:text-white hover:bg-slate-200 dark:hover:bg-sky-900"
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default MultiTextFilter;
