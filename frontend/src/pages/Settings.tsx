import React, { useEffect, useState } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import ClipLoader from 'react-spinners/ClipLoader';
import toast from 'react-hot-toast';
import Breadcrumb from '../components/Breadcrumbs/Breadcrumb';
import { requiredStringField, optionalStringField } from '../utils/form';
import { api } from '../api/axios';
import DefaultPfp from '../images/user/default.jpg';
import { useAuth } from '../contexts/AuthContext';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store/store';
import { setUser } from '../store/slices/authSlice';

const infoSchema = z.object({
  username: requiredStringField('Username'),
  first_name: requiredStringField('First name'),
  last_name: requiredStringField('Last name'),
  bio: optionalStringField(),
  avatar: z.instanceof(FileList).optional(),
});

const pwdSchema = z
  .object({
    old_password: requiredStringField('Old password'),
    new_password1: requiredStringField('New password'),
    new_password2: requiredStringField('New password confirmation'),
  })
  .refine((data) => data.new_password1 === data.new_password2, {
    message: 'The two new password fields do not match',
    path: ['new_password2'],
  });

type PersonalInfoSchema = z.infer<typeof infoSchema>;
type ResetPwdSchema = z.infer<typeof pwdSchema>;

const Settings = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { user } = useAuth();

  // Personal Info
  const [initialValues, setInitialValues] = useState<PersonalInfoSchema | null>(
    null,
  );
  const [avatarModified, setAvatarModified] = useState<boolean>(false);
  const [avatar, setAvatar] = useState<string | null>(null);
  const [previewAvatarUrl, setPreviewAvatarUrl] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    reset,
    clearErrors,
    setValue,
    watch,
    formState: { errors, dirtyFields, isSubmitting },
  } = useForm<PersonalInfoSchema>({
    resolver: zodResolver(infoSchema),
  });

  const currentInfoValues = watch();
  const currentInfoTextValues = { ...currentInfoValues };
  delete currentInfoTextValues.avatar;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAvatar(null);
    setAvatarModified(true);
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      // Checking file type (JPEG or PNG)
      if (!['image/jpeg', 'image/png'].includes(file.type)) {
        setError('avatar', {
          type: 'manual',
          message: 'Only JPEG or PNG files are allowed',
        });
        setValue('avatar', undefined);
      } else if (file.size > 2000000) {
        // Checking file size (2MB)
        setError('avatar', {
          type: 'manual',
          message: 'File size must be less than or equal to 2MB',
        });
        setValue('avatar', undefined);
      } else {
        // Clearing previous errors
        clearErrors('avatar');
        setPreviewAvatarUrl(URL.createObjectURL(file));
      }
    } else {
      // clearing the file and errors if no file is selected,
      setValue('avatar', undefined);
      clearErrors('avatar');
    }
  };

  const handleFileClear = () => {
    setValue('avatar', undefined);
    clearErrors('avatar');
    setPreviewAvatarUrl(null);
    setAvatar(null);
    setAvatarModified(true);
  };

  const onSubmit: SubmitHandler<PersonalInfoSchema> = async (data) => {
    const formData = new FormData();
    formData.append('username', data.username);
    formData.append('first_name', data.first_name);
    formData.append('last_name', data.last_name);
    formData.append('bio', data.bio || JSON.stringify(null));
    if (data.avatar && data.avatar?.length > 0) {
      formData.append('avatar', data.avatar[0]);
    } else if (!data.avatar && !avatar) {
      formData.append('avatar_deleted', '');
    }
    try {
      const res = await api.put(`/auth/user/`, formData, {
        headers: { 'Content-type': 'multipart/form-data' },
      });
      dispatch((dispatch, getState) => {
        const { auth } = getState();
        dispatch(
          setUser({
            ...auth,
            user: res.data,
          }),
        );
      });
      toast.success('Your profile has been successfully updated!', {
        duration: 5000,
      });
    } catch (error: any) {
      if (error.response && error.response.status === 400) {
        (
          Object.keys(error.response.data) as Array<keyof PersonalInfoSchema>
        ).forEach((field) => {
          setError(field, { message: error.response.data[field] });
        });
      } else {
        setError('root', {
          message: 'Something went wrong, please try again later.',
        });
      }
    }
  };

  const infoHasChanges = () => {
    if (avatarModified) return true;
    if (!initialValues || !currentInfoTextValues) return false;
    return (Object.keys(dirtyFields) as Array<keyof PersonalInfoSchema>).some(
      (key) => {
        return initialValues[key] !== currentInfoTextValues[key];
      },
    );
  };

  // Reset Password
  const {
    register: registerPwd,
    handleSubmit: handleSubmitPwd,
    setError: setErrorPwd,
    watch: watchPwd,
    formState: { errors: errorsPwd, isSubmitting: isSubmittingPwd },
  } = useForm<ResetPwdSchema>({ resolver: zodResolver(pwdSchema) });

  const currentPwdValues = watchPwd();

  const pwdFieldsBlank = () => {
    if (!currentPwdValues) return true;
    return (Object.keys(currentPwdValues) as Array<keyof ResetPwdSchema>).some(
      (key) => {
        return currentPwdValues[key] === '';
      },
    );
  };

  const onPwdSubmit: SubmitHandler<ResetPwdSchema> = async (data) => {
    try {
      const res = await api.post('/auth/user/change-password/', data);
      dispatch(setUser(res.data));
      toast.success('Your password has been successfully changed!', {
        duration: 5000,
      });
    } catch (error: any) {
      console.log('Error during form submission:', error);
      if (error.response && error.response.status === 400) {
        (
          Object.keys(error.response.data) as Array<
            'old_password' | 'new_password1' | 'new_password2' | 'new_password'
          >
        ).forEach((field) => {
          if (field === 'new_password') {
            setErrorPwd('root', { message: error.response.data[field] });
          } else {
            setErrorPwd(field, { message: error.response.data[field] });
          }
        });
      } else {
        setErrorPwd('root', {
          message: 'Something went wrong, please try again later.',
        });
      }
    }
  };

  useEffect(() => {
    const loadData = () => {
      if (user) {
        if (user.avatar) setAvatar(user.avatar);
        const formData = {
          ...user,
          bio: user.bio === null ? '' : user.bio,
          avatar:
            typeof user.avatar === 'string' || !user.avatar
              ? undefined
              : user.avatar,
        };
        setInitialValues(formData);
        reset(formData);
      }
    };

    loadData();
  }, [user]);

  useEffect(() => {
    infoHasChanges();
  }, [user, initialValues, currentInfoTextValues]);

  useEffect(() => {
    pwdFieldsBlank();
  }, [currentPwdValues]);

  useEffect(() => {
    return () => {
      if (previewAvatarUrl) {
        URL.revokeObjectURL(previewAvatarUrl);
      }
    };
  }, [previewAvatarUrl]);

  return (
    <>
      <div className="mx-auto max-w-270">
        <Breadcrumb main={user && user.username} pageName="Settings" />

        <div className="grid grid-cols-5 gap-8">
          {/* Personal Information */}
          <div className="col-span-5 xl:col-span-3">
            <div className="w-full border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
              <div className="border-b border-stroke py-4 px-7 dark:border-strokedark">
                <h3 className="font-medium text-black dark:text-white">
                  Personal Information
                </h3>
              </div>
              <div className="p-7">
                <form onSubmit={handleSubmit(onSubmit)}>
                  {/* Username */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="Username"
                    >
                      Username
                    </label>
                    <div className="relative">
                      <span className="absolute left-4.5 top-4">
                        <svg
                          className="fill-current"
                          width="20"
                          height="20"
                          viewBox="0 0 20 20"
                          fill="none"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <g opacity="0.8">
                            <path
                              fillRule="evenodd"
                              clipRule="evenodd"
                              d="M3.72039 12.887C4.50179 12.1056 5.5616 11.6666 6.66667 11.6666H13.3333C14.4384 11.6666 15.4982 12.1056 16.2796 12.887C17.061 13.6684 17.5 14.7282 17.5 15.8333V17.5C17.5 17.9602 17.1269 18.3333 16.6667 18.3333C16.2064 18.3333 15.8333 17.9602 15.8333 17.5V15.8333C15.8333 15.1703 15.5699 14.5344 15.1011 14.0655C14.6323 13.5967 13.9964 13.3333 13.3333 13.3333H6.66667C6.00363 13.3333 5.36774 13.5967 4.8989 14.0655C4.43006 14.5344 4.16667 15.1703 4.16667 15.8333V17.5C4.16667 17.9602 3.79357 18.3333 3.33333 18.3333C2.8731 18.3333 2.5 17.9602 2.5 17.5V15.8333C2.5 14.7282 2.93899 13.6684 3.72039 12.887Z"
                              fill=""
                            />
                            <path
                              fillRule="evenodd"
                              clipRule="evenodd"
                              d="M9.99967 3.33329C8.61896 3.33329 7.49967 4.45258 7.49967 5.83329C7.49967 7.214 8.61896 8.33329 9.99967 8.33329C11.3804 8.33329 12.4997 7.214 12.4997 5.83329C12.4997 4.45258 11.3804 3.33329 9.99967 3.33329ZM5.83301 5.83329C5.83301 3.53211 7.69849 1.66663 9.99967 1.66663C12.3009 1.66663 14.1663 3.53211 14.1663 5.83329C14.1663 8.13448 12.3009 9.99996 9.99967 9.99996C7.69849 9.99996 5.83301 8.13448 5.83301 5.83329Z"
                              fill=""
                            />
                          </g>
                        </svg>
                      </span>
                      <input
                        className="w-full rounded border border-stroke bg-gray py-3 pl-11.5 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        type="text"
                        {...register('username')}
                      />
                    </div>
                    {errors.username && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.username.message}
                      </p>
                    )}
                  </div>

                  {/* First & Last Name */}
                  <div className="mb-5.5 flex flex-col gap-5.5 sm:flex-row">
                    {/* First Name */}
                    <div className="w-full sm:w-1/2">
                      <label
                        className="mb-3 block text-sm font-medium text-black dark:text-white"
                        htmlFor="firstName"
                      >
                        First Name
                      </label>

                      <input
                        className="w-full rounded border border-stroke bg-gray py-3 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        type="text"
                        {...register('first_name')}
                      />
                      {errors.first_name && (
                        <p className="text-red-500 font-medium text-sm italic mt-2">
                          {errors.first_name.message}
                        </p>
                      )}
                    </div>

                    {/* Last Name */}
                    <div className="w-full sm:w-1/2">
                      <label
                        className="mb-3 block text-sm font-medium text-black dark:text-white"
                        htmlFor="lastName"
                      >
                        Last Name
                      </label>
                      <input
                        className="w-full rounded border border-stroke bg-gray py-3 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        type="text"
                        {...register('last_name')}
                      />
                      {errors.last_name && (
                        <p className="text-red-500 font-medium text-sm italic mt-2">
                          {errors.last_name.message}
                        </p>
                      )}
                    </div>
                  </div>
                  {/* Bio */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="bio"
                    >
                      BIO
                    </label>
                    <div className="relative">
                      <span className="absolute left-4.5 top-4">
                        <svg
                          className="fill-current"
                          width="20"
                          height="20"
                          viewBox="0 0 20 20"
                          fill="none"
                          xmlns="http://www.w3.org/2000/svg"
                        >
                          <g opacity="0.8" clipPath="url(#clip0_88_10224)">
                            <path
                              fillRule="evenodd"
                              clipRule="evenodd"
                              d="M1.56524 3.23223C2.03408 2.76339 2.66997 2.5 3.33301 2.5H9.16634C9.62658 2.5 9.99967 2.8731 9.99967 3.33333C9.99967 3.79357 9.62658 4.16667 9.16634 4.16667H3.33301C3.11199 4.16667 2.90003 4.25446 2.74375 4.41074C2.58747 4.56702 2.49967 4.77899 2.49967 5V16.6667C2.49967 16.8877 2.58747 17.0996 2.74375 17.2559C2.90003 17.4122 3.11199 17.5 3.33301 17.5H14.9997C15.2207 17.5 15.4326 17.4122 15.5889 17.2559C15.7452 17.0996 15.833 16.8877 15.833 16.6667V10.8333C15.833 10.3731 16.2061 10 16.6663 10C17.1266 10 17.4997 10.3731 17.4997 10.8333V16.6667C17.4997 17.3297 17.2363 17.9656 16.7674 18.4344C16.2986 18.9033 15.6627 19.1667 14.9997 19.1667H3.33301C2.66997 19.1667 2.03408 18.9033 1.56524 18.4344C1.0964 17.9656 0.833008 17.3297 0.833008 16.6667V5C0.833008 4.33696 1.0964 3.70107 1.56524 3.23223Z"
                              fill=""
                            />
                            <path
                              fillRule="evenodd"
                              clipRule="evenodd"
                              d="M16.6664 2.39884C16.4185 2.39884 16.1809 2.49729 16.0056 2.67253L8.25216 10.426L7.81167 12.188L9.57365 11.7475L17.3271 3.99402C17.5023 3.81878 17.6008 3.5811 17.6008 3.33328C17.6008 3.08545 17.5023 2.84777 17.3271 2.67253C17.1519 2.49729 16.9142 2.39884 16.6664 2.39884ZM14.8271 1.49402C15.3149 1.00622 15.9765 0.732178 16.6664 0.732178C17.3562 0.732178 18.0178 1.00622 18.5056 1.49402C18.9934 1.98182 19.2675 2.64342 19.2675 3.33328C19.2675 4.02313 18.9934 4.68473 18.5056 5.17253L10.5889 13.0892C10.4821 13.196 10.3483 13.2718 10.2018 13.3084L6.86847 14.1417C6.58449 14.2127 6.28409 14.1295 6.0771 13.9225C5.87012 13.7156 5.78691 13.4151 5.85791 13.1312L6.69124 9.79783C6.72787 9.65131 6.80364 9.51749 6.91044 9.41069L14.8271 1.49402Z"
                              fill=""
                            />
                          </g>
                          <defs>
                            <clipPath id="clip0_88_10224">
                              <rect width="20" height="20" fill="white" />
                            </clipPath>
                          </defs>
                        </svg>
                      </span>

                      <textarea
                        className="w-full rounded border border-stroke bg-gray py-3 pl-11.5 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        {...register('bio')}
                        rows={6}
                        placeholder="Write your bio here"
                      ></textarea>
                    </div>
                    {errors.bio && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.bio.message}
                      </p>
                    )}
                  </div>
                  {/* Photo */}
                  <div className="mb-5.5">
                    <label
                      className="mb-5 block text-base font-medium text-black dark:text-white border-b border-stroke py-3 dark:border-strokedark"
                      htmlFor="bio"
                    >
                      Your Photo
                    </label>
                    <div className="mb-4 flex items-center gap-3 ">
                      <div className="h-15 w-15 rounded-full">
                        {previewAvatarUrl ? (
                          <img
                            src={previewAvatarUrl}
                            className="w-full h-full object-cover rounded-full"
                            alt="User"
                          />
                        ) : (
                          <img
                            src={avatar || DefaultPfp}
                            className="w-full h-full object-cover rounded-full"
                            alt="User"
                          />
                        )}
                      </div>
                      <div>
                        <span className="mb-1.5 text-black dark:text-white">
                          Edit your photo
                        </span>
                        <span className="mt-2 flex gap-2.5">
                          {(avatar || previewAvatarUrl) && (
                            <button
                              onClick={handleFileClear}
                              type="button"
                              className="bg-red-500 hover:bg-red-700 text-white text-sm font-bold py-1 px-3 rounded"
                            >
                              Delete
                            </button>
                          )}
                          <input
                            type="file"
                            {...register('avatar')}
                            onChange={handleFileChange}
                            accept="image/*"
                            className="text-sm font-bold rounded
                                        cursor-pointer
                                        file:me-2 file:py-1 file:px-4
                                        file:cursor-pointer
                                        file:border-0
                                        file:bg-slate-500 file:text-white
                                        hover:file:bg-slate-600
                                        dark:file:bg-slate-500
                                        dark:hover:file:bg-slate-600"
                          />
                        </span>
                      </div>
                    </div>
                    {errors.avatar && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.avatar.message}
                      </p>
                    )}
                  </div>
                  {errors.root && (
                    <div className="text-center mb-3">
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.root.message}
                      </p>
                    </div>
                  )}
                  <div className="flex justify-end gap-4.5">
                    <button
                      className={
                        'flex justify-center ' +
                        (!infoHasChanges()
                          ? 'cursor-not-allowed bg-blue-400 '
                          : 'bg-primary hover:bg-opacity-90 ') +
                        'rounded py-2 px-6 font-medium text-gray'
                      }
                      type="submit"
                      disabled={!infoHasChanges() || isSubmitting}
                    >
                      {isSubmitting ? (
                        <ClipLoader color="#ffffff" size={23} />
                      ) : (
                        'Save'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          {/* Reset Password */}
          <div className="col-span-5 xl:col-span-2">
            <div className="rounded-sm border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
              <div className="border-b border-stroke py-4 px-7 dark:border-strokedark">
                <h3 className="font-medium text-black dark:text-white">
                  Reset Password
                </h3>
              </div>
              <div className="p-7">
                <form onSubmit={handleSubmitPwd(onPwdSubmit)}>
                  {/* Old Password */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="Password"
                    >
                      Password
                    </label>
                    <div className="relative">
                      <input
                        className="w-full rounded border border-stroke bg-gray py-3 pl-4 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        type="password"
                        {...registerPwd('old_password')}
                      />
                    </div>
                    {errorsPwd.old_password && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errorsPwd.old_password.message}
                      </p>
                    )}
                  </div>
                  {/* New Password */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="newPassword"
                    >
                      New Password
                    </label>
                    <div className="relative">
                      <input
                        className="w-full rounded border border-stroke bg-gray py-3 pl-4 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        type="password"
                        {...registerPwd('new_password1')}
                      />
                    </div>
                    {errorsPwd.new_password1 && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errorsPwd.new_password1.message}
                      </p>
                    )}
                  </div>
                  {/* Re-Type New Password */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="newPassword2"
                    >
                      Re-Type New Password
                    </label>
                    <div className="relative">
                      <input
                        className="w-full rounded border border-stroke bg-gray py-3 pl-4 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        type="password"
                        {...registerPwd('new_password2')}
                      />
                    </div>
                    {errorsPwd.new_password2 && (
                      <div>
                        {Array.isArray(errorsPwd.new_password2.message) ? (
                          errorsPwd.new_password2.message.map(
                            (errorMessage: string, index: number) => (
                              <p
                                key={index}
                                className="text-red-500 font-medium text-sm italic mt-2"
                              >
                                {errorMessage}
                              </p>
                            ),
                          )
                        ) : (
                          <p className="text-red-500 font-medium text-sm italic mt-2">
                            {errorsPwd.new_password2.message}
                          </p>
                        )}
                      </div>
                    )}
                    {errorsPwd.root && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errorsPwd.root.message}
                      </p>
                    )}
                  </div>

                  <div className="flex justify-end gap-4.5">
                    <button
                      className={
                        'flex justify-center ' +
                        (pwdFieldsBlank()
                          ? 'cursor-not-allowed bg-blue-400 '
                          : 'bg-primary hover:bg-opacity-90 ') +
                        'rounded py-2 px-6 font-medium text-gray'
                      }
                      type="submit"
                      disabled={pwdFieldsBlank() || isSubmittingPwd}
                    >
                      {isSubmittingPwd ? (
                        <ClipLoader color="#ffffff" size={23} />
                      ) : (
                        'Save'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Settings;
