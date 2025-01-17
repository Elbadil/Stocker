import { useEffect, useState } from 'react';
import Activity from './Activity';
import Breadcrumb from '../../components/Breadcrumbs/Breadcrumb';
import Loader from '../../common/Loader';
import { api } from '../../api/axios';
import ClipLoader from 'react-spinners/ClipLoader';

export interface ActivityProps {
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

const ActivityLog = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [activities, setActivities] = useState<ActivityProps[]>([]);
  const [nextActivitiesLink, setNextActivitiesLink] = useState<string | null>(
    null,
  );

  const loadMore = async (nextLink: string) => {
    console.log(nextLink);
    setLoadingMore(true);
    try {
      const res = await api.get(nextLink);
      console.log(res.data);
      setActivities((prev) => [...prev, ...res.data.results]);
      setNextActivitiesLink(res.data.next);
    } catch (error: any) {
      console.log('Error fetching user activities', error);
    } finally {
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const res = await api.get('/auth/user/activities/');
        setActivities(res.data.results);
        setNextActivitiesLink(res.data.next);
      } catch (error: any) {
        console.log('Error fetching user activities', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return (
    <div className="mx-auto max-w-full">
      <Breadcrumb main="Activity Log" pageName="Activities" />
      {loading ? (
        <Loader />
      ) : (
        <>
          <div className="col-span-5 xl:col-span-3 relative">
            <div className="w-full flex flex-col border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
              <div className="p-3 flex-grow">
                {/* Activity List */}
                {activities.map((activity) => (
                  <Activity
                    key={activity.id}
                    user={activity.user}
                    action={activity.action}
                    modelName={activity.model_name}
                    objectRef={activity.object_ref}
                    createdAt={activity.created_at}
                  />
                ))}
              </div>
              {nextActivitiesLink && (
                <div className='flex justify-center'>
                  <div
                    onClick={() => loadMore(nextActivitiesLink)}
                    className="text-base font-medium px-7.5 pt-1 pb-5 text-meta-5 hover:underline cursor-pointer"
                  >
                    {loadingMore ? (
                      <ClipLoader color="#259ae6" />
                    ) : (
                      'load more activities'
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ActivityLog;
