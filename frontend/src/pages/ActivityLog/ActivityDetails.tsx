import React from 'react';
import { capitalizeFirstLetter } from '../../utils/form';

interface ActivityDetails {
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  action: string;
  modelName: string;
  objectList: string[];
  createdAt: string;
}

const ActivityDetails = ({
  setOpen,
  modelName,
  action,
  objectList,
  createdAt,
}: ActivityDetails) => {
  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Modal Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          {capitalizeFirstLetter(action)} {modelName} records
        </h3>
        <div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-hidden={true}
          >
            <span className="text-slate-400 hover:text-slate-700 dark:text-white dark:hover:text-slate-300">
              ✖
            </span>
          </button>
        </div>
      </div>
      {/* Content */}
      <div className="max-w-full overflow-y-auto max-h-[80vh] flex flex-col">
        <div className="p-6">
          <p className="mb-4 text-slate-600 dark:text-slate-400">
            {capitalizeFirstLetter(action)} at {createdAt}
          </p>
          <ol className="mb-2 list-inside list-disc text-black dark:text-white">
            {objectList.map((object, index: number) => (
              <li className={`${index !== 0 ? 'mt-2' : ''}`} key={index}>
                {capitalizeFirstLetter(modelName)}
                {modelName.includes('order') ? ' with reference ID: ' : ' '}
                <strong>{object}</strong>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
};

export default ActivityDetails;
