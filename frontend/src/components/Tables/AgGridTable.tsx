import { AgGridReact } from '@ag-grid-community/react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { forwardRef, useCallback, useMemo } from 'react';
import {
  ColDef,
  GridOptions,
  RowSelectionOptions,
  IDateFilterParams,
  ITextFilterParams,
  INumberFilterParams,
  GetRowIdParams,
} from '@ag-grid-community/core'
import { useAlert } from '../../contexts/AlertContext';
import { ClientSideRowModelModule } from '@ag-grid-community/client-side-row-model';
import { ModuleRegistry } from '@ag-grid-community/core';

ModuleRegistry.registerModules([ClientSideRowModelModule]);

export interface AgGridTableProps {
  rowData: [];
  colDefs: ColDef[];
  searchTerm: string;
  [key: string]: any;
}

export const dateFilterParams: IDateFilterParams = {
  comparator: (filterLocalDateAtMidnight: Date, cellValue: string) => {
    var dateAsString = cellValue;
    if (dateAsString == null) return -1;
    var dateParts = dateAsString.split('/');
    var cellDate = new Date(
      Number(dateParts[2]),
      Number(dateParts[1]) - 1,
      Number(dateParts[0]),
    );
    if (filterLocalDateAtMidnight.getTime() === cellDate.getTime()) {
      return 0;
    }
    if (cellDate < filterLocalDateAtMidnight) {
      return -1;
    }
    if (cellDate > filterLocalDateAtMidnight) {
      return 1;
    }
    return 0;
  },
  inRangeFloatingFilterDateFormat: 'Do MMM YYYY',
};

const AgGridTable = forwardRef<AgGridReact, AgGridTableProps>(
  ({ rowData, colDefs, searchTerm, ...otherProps }, ref) => {
    const { isDarkMode } = useAlert();

    const defaultColDef = useMemo(() => {
      return {
        flex: 1,
        minWidth: 130,
        filterParams: {
          inRangeInclusive: true,
          buttons: ['apply', 'reset'],
          closeOnApply: true,
        } as ITextFilterParams | INumberFilterParams | IDateFilterParams,
        filter: true,
        sortable: true,
        autoHeight: true,
        headerClass: 'text-base font-medium',
        cellClass: 'font-medium',
      };
    }, []);

    const rowSelection = useMemo<
      RowSelectionOptions | 'single' | 'multiple'
    >(() => {
      return {
        mode: 'multiRow',
        selectAll: 'currentPage',
        enableSelectionWithoutKeys: true,
        // enableClickSelection: true,
      };
    }, []);

    const gridOptions: GridOptions = {
      domLayout: 'autoHeight',
      pagination: true,
      paginationPageSize: 20,
      enableCellTextSelection: true,
    };

    const getRowId = useCallback(
      (params: GetRowIdParams) => String(params.data.id),
      [],
    );

    return (
      <div
        className={`ag-theme-${
          isDarkMode ? 'quartz-dark' : 'quartz'
        } w-full flex-grow font-satoshi`}
      >
        <AgGridReact
          ref={ref}
          rowData={rowData}
          columnDefs={colDefs}
          rowSelection={rowSelection}
          defaultColDef={defaultColDef}
          gridOptions={gridOptions}
          quickFilterText={searchTerm}
          getRowId={getRowId}
          {...otherProps}
        />
      </div>
    );
  },
);

export default AgGridTable;
