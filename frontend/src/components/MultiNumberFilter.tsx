import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import { IDoesFilterPassParams } from '@ag-grid-community/core';
import { CustomFilterProps, useGridFilter } from '@ag-grid-community/react';
import { useCallback, useRef, useState } from 'react';
import { useAlert } from '../contexts/AlertContext';

type ContainerType =
  | 'columnMenu'
  | 'contextMenu'
  | 'toolPanel'
  | 'floatingFilter'
  | 'columnFilter';

interface IAfterGuiAttachedParams {
  // Where this component is attached to.
  container?: ContainerType;
  // Call this to hide the popup.
  // i.e useful if your component has an action button and you want to hide the popup after it is pressed.
  hidePopup?: () => void;
  // Set to `true` to not have the component focus its default item.
  suppressFocus?: boolean;
}

const MultiNumberFilter = ({
  model,
  onModelChange,
  getValue,
}: CustomFilterProps) => {
  const { isDarkMode } = useAlert();
  const inputRef = useRef<HTMLInputElement>(null);
  const [filterType, setFilterType] = useState<string>('equals');
  const [inputValue, setInputValue] = useState<string>('');
  const [secondInputValue, setSecondInputValue] = useState<string | null>(null);
  const hidePopupRef = useRef<(() => void) | null>(null);

  const doesFilterPass = useCallback(
    ({ node }: IDoesFilterPassParams) => {
      const cellValue = getValue(node) || [];
      const filterValue = Number(model);
      if (filterValue !== null && filterValue !== undefined) {
        switch (filterType) {
          case 'equals':
            return cellValue.some((value: number) => value === filterValue);
          case 'greaterThan':
            return cellValue.some((value: number) => value > filterValue);
          case 'lessThan':
            return cellValue.some((value: number) => value < filterValue);
          case 'between':
            if (secondInputValue !== null && secondInputValue !== undefined) {
              return cellValue.some(
                (value: number) =>
                  value >= filterValue && value <= Number(secondInputValue),
              );
            }
            return false;
          default:
            return false;
        }
      }
      return false;
    },
    [model, filterType, getValue, secondInputValue],
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
    onModelChange(inputValue || null);
    if (hidePopupRef.current) hidePopupRef.current();
  };

  const clearFilter = () => {
    setInputValue('');
    setSecondInputValue('');
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
            <option value="equals">Equals</option>
            <option value="greaterThan">Greater Than</option>
            <option value="lessThan">Less Than</option>
            <option value="between">Between</option>
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
            type="number"
            ref={inputRef}
            value={inputValue || ''}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={filterType === 'between' ? 'from' : 'Filter...'}
            className="w-full py-1.5 pl-5.5 appearance-none bg-white dark:bg-customDark rounded-md border-2 border-stroke focus:border-blue-400 focus-visible:outline-none dark:focus:border-blue-400 dark:border-strokedark no-arrows"
            style={{
              MozAppearance: 'textfield',
              WebkitAppearance: 'none',
            }}
          />
        </div>
        {filterType === 'between' && (
          <div className=" relative mb-2">
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
              type="number"
              ref={inputRef}
              value={secondInputValue || ''}
              onChange={(e) => setSecondInputValue(e.target.value)}
              placeholder="to"
              className="w-full py-1.5 pl-5.5 bg-white dark:bg-customDark rounded-md border-2 border-stroke focus:border-blue-400 focus-visible:outline-none dark:focus:border-blue-400 dark:border-strokedark no-arrows"
            />
          </div>
        )}
      </div>
      <div className="mt-5 mb-1 flex justify-end gap-5">
        <button
          onClick={applyFilter}
          className="bg-white dark:bg-customDark border-1 py-2.5 px-5 rounded-sm text-center text-black dark:text-white dark:border-strokedark hover:bg-opacity-90 lg:px-4 xl:px-4"
        >
          Apply
        </button>
        <button
          onClick={clearFilter}
          className="bg-white dark:bg-customDark border-1 py-2.5 px-5 rounded-sm text-center text-black dark:text-white dark:border-strokedark hover:bg-opacity-90 lg:px-4 xl:px-4"
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default MultiNumberFilter;
