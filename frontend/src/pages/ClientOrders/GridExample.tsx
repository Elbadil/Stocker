import { ClientSideRowModelModule } from '@ag-grid-community/client-side-row-model';
// Theme
import {
  ColDef,
  IDoesFilterPassParams,
  ModuleRegistry,
} from '@ag-grid-community/core';
import {
  AgGridReact,
  CustomFilterProps,
  useGridFilter,
} from '@ag-grid-community/react';
// React Grid Logic
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import React, { useCallback, useState } from 'react';
import Breadcrumb from '../../components/Breadcrumbs/Breadcrumb';

ModuleRegistry.registerModules([ClientSideRowModelModule]);

// Row Data Interface
interface IRow {
  make: string;
  model: string;
  price: number;
  electric: boolean;
}

export const CustomFilter = ({
  model,
  onModelChange,
}: CustomFilterProps) => {
  const valueChanged = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      onModelChange(newValue == '' ? null : newValue);
    },
    [model],
  );

  const doesFilterPass = useCallback(
    (params: IDoesFilterPassParams) => {
      console.log(params);
      return true;
    },
    [model],
  );

  useGridFilter({ doesFilterPass });

  return (
    <>
      <input type="text" value={model || ''} onChange={valueChanged} />
    </>
  );
};

// Create new GridExample component
const GridExample = () => {
  // Row Data: The data to be displayed.
  const [rowData] = useState<IRow[]>([
    { make: 'Tesla', model: 'Model Y', price: 64950, electric: true },
    { make: 'Ford', model: 'F-Series', price: 33850, electric: false },
    { make: 'Toyota', model: 'Corolla', price: 29600, electric: false },
    { make: 'Mercedes', model: 'EQA', price: 48890, electric: true },
    { make: 'Fiat', model: '500', price: 15774, electric: false },
    { make: 'Nissan', model: 'Juke', price: 20675, electric: false },
  ]);

  // Column Definitions: Defines & controls grid columns.
  const [colDefs] = useState<ColDef<IRow>[]>([
    { field: 'make', filter: CustomFilter },
    { field: 'model' },
    { field: 'price' },
    { field: 'electric' },
  ]);

  const defaultColDef: ColDef = {
    flex: 1,
    filter: true,
  };

  // Container: Defines the grid's theme & dimensions.
  return (
    <>
      <div className="mx-auto max-w-full">
        <Breadcrumb main="Client Orders" pageName="Orders" />
        <div className="col-span-5 xl:col-span-3 relative">
          <div
            className={'ag-theme-quartz-dark'}
            style={{ width: '100%', height: '500px' }}
          >
            <AgGridReact
              rowData={rowData}
              columnDefs={colDefs}
              defaultColDef={defaultColDef}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default GridExample;
