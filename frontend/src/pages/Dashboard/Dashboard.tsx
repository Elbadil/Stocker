import { useEffect, useState } from 'react';
import AttachMoneyOutlinedIcon from '@mui/icons-material/AttachMoneyOutlined';
import ShoppingCartOutlinedIcon from '@mui/icons-material/ShoppingCartOutlined';
import InventoryOutlinedIcon from '@mui/icons-material/InventoryOutlined';
import LoyaltyOutlinedIcon from '@mui/icons-material/LoyaltyOutlined';
import CardDataStats from '../../components/CardDataStats';
import ChartOne from '../../components/Charts/ChartOne';
import ChartTwo from '../../components/Charts/ChartTwo';
import RecentActivitiesCard from '../../components/Cards/RecentActivitiesCard';
import TableOne from '../../components/Tables/TableOne';
import { useAlert } from '../../contexts/AlertContext';
import { Alert } from '../UiElements/Alert';
import { api } from '../../api/axios';
import Loader from '../../common/Loader';

interface DashboardData {
  total_items: number;
  total_sales: number;
  active_sales_orders: number;
  total_profit: number;
}

const Dashboard: React.FC = () => {
  const { alert } = useAlert();
  const [loading, setLoading] = useState<boolean>(true);
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    total_items: 0,
    total_sales: 0,
    active_sales_orders: 0,
    total_profit: 0,
  });

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const res = await api.get('/dashboard/?info=general');
        setDashboardData(res.data);
      } catch (error: any) {
        console.log('Error fetching dashboard data', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return loading ? (
    <Loader />
  ) : (
    <>
      {alert && <Alert {...alert} />}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
        <CardDataStats
          title="Total Profit"
          total={`${dashboardData.total_profit.toFixed(2)} MAD`}
          link="/sales"
        >
          <AttachMoneyOutlinedIcon sx={{ fontSize: '28px' }} />
        </CardDataStats>
        <CardDataStats
          title="Total Sales"
          total={dashboardData.total_sales}
          link="/sales"
        >
          <LoyaltyOutlinedIcon sx={{ fontSize: '28px', paddingTop: '2px' }} />
        </CardDataStats>
        <CardDataStats
          title="Active Sales | Orders"
          total={dashboardData.active_sales_orders}
        >
          <ShoppingCartOutlinedIcon sx={{ fontSize: '27px' }} />
        </CardDataStats>
        <CardDataStats
          title="Total Items"
          total={dashboardData.total_items}
          link="/inventory/items"
        >
          <InventoryOutlinedIcon sx={{ fontSize: '28px' }} />
        </CardDataStats>
      </div>

      <div className="mt-4 grid grid-cols-12 gap-4 md:mt-6 md:gap-6 2xl:mt-7.5 2xl:gap-7.5">
        <ChartOne />
        <ChartTwo />
        <div className="col-span-12 xl:col-span-12">
          <TableOne />
        </div>
        <RecentActivitiesCard />
      </div>
    </>
  );
};

export default Dashboard;
