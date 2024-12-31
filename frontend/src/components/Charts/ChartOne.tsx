import { ApexOptions } from 'apexcharts';
import React, { useEffect, useState } from 'react';
import ReactApexChart from 'react-apexcharts';
import { api } from '../../api/axios';

const defaultOptions: ApexOptions = {
  legend: {
    show: false,
    position: 'top',
    horizontalAlign: 'left',
  },
  colors: ['#F87185', '#3C50E0'],
  chart: {
    fontFamily: 'Satoshi, sans-serif',
    height: 335,
    type: 'area',
    dropShadow: {
      enabled: true,
      color: '#623CEA14',
      top: 10,
      blur: 4,
      left: 0,
      opacity: 0.1,
    },

    toolbar: {
      show: false,
    },
  },
  responsive: [
    {
      breakpoint: 1024,
      options: {
        chart: {
          height: 300,
        },
      },
    },
    {
      breakpoint: 1366,
      options: {
        chart: {
          height: 350,
        },
      },
    },
  ],
  stroke: {
    width: [2, 2],
    curve: 'straight',
  },
  // labels: {
  //   show: false,
  //   position: "top",
  // },
  grid: {
    xaxis: {
      lines: {
        show: true,
      },
    },
    yaxis: {
      lines: {
        show: true,
      },
    },
  },
  dataLabels: {
    enabled: false,
  },
  markers: {
    size: 4,
    colors: '#fff',
    strokeColors: ['#F87185', '#3056D3'],
    strokeWidth: 3,
    strokeOpacity: 0.9,
    strokeDashArray: 0,
    fillOpacity: 1,
    discrete: [],
    hover: {
      size: undefined,
      sizeOffset: 5,
    },
  },
  yaxis: {
    title: {
      style: {
        fontSize: '0px',
      },
    },
    min: 0,
    max: 10,
  },
  noData: {
    text: 'Loading...',
    align: 'center',
    verticalAlign: 'middle',
    offsetX: 0,
    offsetY: 0,
    style: {
      color: '#000000',
      fontSize: '14px',
      fontFamily: 'Satoshi, sans-serif',
    },
  },
};

const ChartOne: React.FC = () => {
  const [currentFilter, setCurrentFilter] = useState<string>('week');
  const [categories, setCategories] = useState<string[]>([
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
    'Sun',
  ]);
  const [series, setSeries] = useState<ApexAxisChartSeries>([]);
  const [dateRange, setDateRange] = useState<string>('');

  const options: ApexOptions = {
    ...defaultOptions,
    xaxis: {
      type: currentFilter === 'month' ? 'datetime': 'category',
      categories: categories,
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false,
      },
      tickAmount: 10,
    },
  };

  useEffect(() => {
    const loadData = async (period: string) => {
      setCategories([]);
      setSeries([]);
      try {
        const res = await api.get(
          `/dashboard/sales_analytics/?period=${period}`,
        );
        const { categories, series, date_range } = res.data;
        setCategories(categories);
        setDateRange(date_range);
        setSeries(series);
      } catch (error: any) {
        console.log('Error fetching sales analytics', error);
      }
    };

    loadData(currentFilter);
  }, [currentFilter]);

  return (
    <div className="col-span-12 rounded-sm border border-stroke bg-white px-5 pt-7.5 pb-5 shadow-default dark:border-strokedark dark:bg-boxdark sm:px-7.5 xl:col-span-8">
      <div className="flex flex-wrap items-start justify-between gap-3 sm:flex-nowrap">
        <div className="flex w-full flex-wrap gap-3 sm:gap-5">
          <div className="flex min-w-47.5">
            <span className="mt-1 mr-2 flex h-4 w-full max-w-4 items-center justify-center rounded-full border border-primary">
              <span className="block h-2.5 w-full max-w-2.5 rounded-full bg-primary"></span>
            </span>
            <div className="w-full">
              <p className="font-semibold text-primary">Completed Sales</p>
              <p className="text-sm font-medium">{dateRange}</p>
            </div>
          </div>
          <div className="flex min-w-47.5">
            <span className="mt-1 mr-2 flex h-4 w-full max-w-4 items-center justify-center rounded-full border border-red-400">
              <span className="block h-2.5 w-full max-w-2.5 rounded-full bg-red-400"></span>
            </span>
            <div className="w-full">
              <p className="font-semibold text-red-400">
                Failed Sales - Orders
              </p>
              <p className="text-sm font-medium">{dateRange}</p>
            </div>
          </div>
        </div>
        <div className="flex w-full max-w-45 justify-end">
          <div className="inline-flex items-center rounded-md bg-whiter p-1.5 dark:bg-meta-4">
            <button
              onClick={() => setCurrentFilter('week')}
              className={`rounded ${
                currentFilter === 'week' &&
                'bg-white dark:bg-boxdark shadow-card'
              } py-1 px-3 text-xs font-medium text-black hover:bg-white hover:shadow-card dark:text-white dark:hover:bg-boxdark`}
            >
              This Week
            </button>
            <button
              onClick={() => setCurrentFilter('month')}
              className={`rounded ${
                currentFilter === 'month' &&
                'bg-white dark:bg-boxdark shadow-card'
              } py-1 px-3 text-xs font-medium text-black hover:bg-white hover:shadow-card dark:text-white dark:hover:bg-boxdark`}
            >
              This Month
            </button>
          </div>
        </div>
      </div>

      <div>
        <div id="chartOne" className="-ml-5">
          <ReactApexChart
            options={options}
            series={series}
            type="area"
            height={350}
          />
        </div>
      </div>
    </div>
  );
};

export default ChartOne;
