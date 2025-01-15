import { useState } from 'react';
import ModalOverlay from '../../components/ModalOverlay';
import Default from '../../images/user/default.jpg';
import ActivityDetails from './ActivityDetails';

interface Activity {
  key: number;
  user: {
    username: string;
    avatar: string | null;
  };
  action: string;
  modelName: string;
  objectRef: string[];
  createdAt: string;
}

const Activity = ({
  key,
  user,
  action,
  modelName,
  objectRef,
  createdAt,
}: Activity) => {
  const [openActivityDetailsOpen, setOpenActivityDetails] =
    useState<boolean>(false);

  let actionColor;

  if (action === 'created') {
    actionColor = 'text-meta-3';
  } else if (action === 'updated') {
    actionColor = 'text-meta-5';
  } else {
    actionColor = 'text-red-400';
  }

  return (
    <div
      className="flex items-center gap-5 py-3 px-3.5 hover:bg-gray-3 dark:hover:bg-meta-4"
      key={key}
    >
      <div className="relative h-14 w-14 rounded-full">
        <img
          className="w-full h-full object-cover rounded-full"
          src={user.avatar || Default}
          alt="User"
        />
      </div>
      <div className="flex flex-1 items-center gap-3 justify-between">
        <div>
          <h5 className="font-medium text-black dark:text-white">
            {user.username}
          </h5>
          <div className="text-sm text-black dark:text-white">
            <span className={`font-medium ${actionColor}`}>{action} </span>
            {objectRef.length > 1 ? (
              <span
                onClick={() => setOpenActivityDetails(true)}
                className="font-medium hover:underline cursor-pointer"
              >
                {objectRef.length} {modelName}s
              </span>
            ) : (
              <span>
                {modelName}
                {modelName.includes('order') ? ' with reference ID: ' : ' '}
                <strong>{objectRef}</strong>
              </span>
            )}
          </div>
        </div>
        <div className="text-xs">{createdAt}</div>
      </div>
      <ModalOverlay
        isOpen={openActivityDetailsOpen}
        onClose={() => setOpenActivityDetails(false)}
      >
        <ActivityDetails
          setOpen={setOpenActivityDetails}
          action={action}
          modelName={modelName}
          objectList={objectRef}
          createdAt={createdAt}
        />
      </ModalOverlay>
    </div>
  );
};

export default Activity;
