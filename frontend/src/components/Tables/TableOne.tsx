import { useEffect, useState } from 'react';
import Default from '../../images/item/default.jpg';
import { api } from '../../api/axios';

interface ItemData {
  picture: string | null;
  name: string;
  total_quantity: number;
  total_profit: number;
  total_revenue: number;
}

const TableOne = () => {
  const [itemData, setItemData] = useState<ItemData[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get('/dashboard/?info=top-selling-items&limit=5');
        setItemData(res.data);
      } catch (error: any) {
        console.log('Error fetching items data', error);
      }
    };

    loadData();
  }, []);

  return (
    <div className="rounded-sm border border-stroke bg-white px-5 pt-6 pb-2.5 shadow-default dark:border-strokedark dark:bg-boxdark sm:px-7.5 xl:pb-1">
      <h4 className="mb-6 text-xl font-semibold text-black dark:text-white">
        Top Selling Items
      </h4>

      <div className="flex flex-col min-h-[10vh]">
        <div className="grid grid-cols-3 rounded-sm bg-gray-2 dark:bg-meta-4 sm:grid-cols-4">
          <div className="p-2.5 xl:p-5">
            <h5 className="text-sm font-medium uppercase xsm:text-base">
              Item
            </h5>
          </div>
          <div className="p-2.5 text-center xl:p-5">
            <h5 className="text-sm font-medium uppercase xsm:text-base">
              Sold Quantity
            </h5>
          </div>
          <div className="p-2.5 text-center xl:p-5">
            <h5 className="text-sm font-medium uppercase xsm:text-base">
              T. Profit
            </h5>
          </div>

          <div className="hidden p-2.5 text-center sm:block xl:p-5">
            <h5 className="text-sm font-medium uppercase xsm:text-base">
              T. Revenue
            </h5>
          </div>
        </div>

        {itemData.length >= 1 ? (
          itemData.map((item, key) => (
            <div
              className={`grid grid-cols-3 sm:grid-cols-4 ${
                key === itemData.length - 1
                  ? ''
                  : 'border-b border-stroke dark:border-strokedark'
              }`}
              key={key}
            >
              <div className="flex items-center gap-3 p-2.5 xl:p-5">
                <div className="h-20 w-20 rounded-full flex-shrink-0">
                  <img
                    className="w-full h-full object-cover rounded-full"
                    src={item.picture || Default}
                    alt="Item"
                  />
                </div>
                <p className="hidden text-black dark:text-white sm:block">
                  {item.name}
                </p>
              </div>

              <div className="flex items-center justify-center p-2.5 xl:p-5">
                <p className="text-black dark:text-white">
                  {item.total_quantity}
                </p>
              </div>

              <div className="flex items-center justify-center p-2.5 xl:p-5">
                <p className="text-meta-3">
                  {item.total_profit.toFixed(2)} MAD
                </p>
              </div>

              <div className="hidden items-center justify-center p-2.5 sm:flex xl:p-5">
                <p className="text-meta-5">
                  {item.total_revenue.toFixed(2)} MAD
                </p>
              </div>
            </div>
          ))
        ) : (
          <div className="p-4 flex justify-center font-medium">No Data</div>
        )}
      </div>
    </div>
  );
};

export default TableOne;
