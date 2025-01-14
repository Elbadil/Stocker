import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Activity from '../../pages/ActivityLog/Activity';
import { api } from '../../api/axios';

interface RecentActivity {
  id: string;
  user: {
    username: string;
    avatar: string | null;
  };
  action: 'created' | 'updated' | 'deleted';
  model_name:
    | 'item'
    | 'client'
    | 'supplier'
    | 'client order'
    | 'supplier order'
    | 'sale';
  object_ref: string[];
  created_at: string;
}

const RecentActivitiesCard = () => {
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>(
    [],
  );

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get('/dashboard/?info=recent-activities&limit=5');
        setRecentActivities(res.data);
      } catch (error: any) {
        console.log('Error fetching recent activities', error);
      }
    };

    loadData();
  }, []);

  return (
    <div className="col-span-12 rounded-sm border border-stroke bg-white py-6 shadow-default dark:border-strokedark dark:bg-boxdark xl:col-span-4">
      <h4 className="mb-6 px-7.5 text-xl font-semibold text-black dark:text-white">
        Recent Activities
      </h4>

      <div className="mb-2">
        {recentActivities.map((activity, key) => (
          <Activity
            key={key}
            user={activity.user}
            action={activity.action}
            modelName={activity.model_name}
            objectRef={activity.object_ref}
            createdAt={activity.created_at}
          />
        ))}
      </div>
      <Link
        to="/activity-log"
        className="text-base font-medium px-7.5 text-meta-5 hover:underline"
      >
        See all activities
      </Link>
    </div>
  );
};

export default RecentActivitiesCard;
