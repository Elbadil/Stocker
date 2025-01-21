import { Link } from 'react-router-dom';
import LogoWhite from '../../images/logo/logo-white.png';
import LogoBlack from '../../images/logo/logo-black.png';
import DarkModeSwitcher from '../Header/DarkModeSwitcher';
import { useAlert } from '../../contexts/AlertContext';

const AuthHeader = () => {
  const { isDarkMode } = useAlert();

  return (
    <header className="sticky top-0 z-999 flex w-full bg-white drop-shadow-1 dark:bg-boxdark dark:drop-shadow-none">
      <div className="flex flex-grow items-center justify-between px-4 py-4 shadow-2 md:px-6 2xl:px-11">
        <Link to="/">
          <img
            className="ml-2 w-35 lg:w-49"
            src={`${isDarkMode ? LogoWhite : LogoBlack}`}
          />
        </Link>
        <div className="flex items-center gap-3 2xsm:gap-7">
          <ul className="flex items-center gap-3 2xsm:gap-3">
            {/* <!-- Dark Mode Toggler --> */}
            <DarkModeSwitcher />
            <Link
              to="/auth/login"
              className="inline-flex items-center justify-center rounded-md bg-primary py-1.5 px-2 text-center font-medium text-white hover:bg-opacity-90 lg:px-4 xl:px-4"
            >
              Login
            </Link>
            <Link
              to="/auth/signup"
              className="inline-flex items-center justify-center rounded-md bg-meta-3 py-1.5 px-2 text-center font-medium text-white hover:bg-opacity-90 lg:px-4 xl:px-4"
            >
              Sign Up
            </Link>
            {/* <!-- Dark Mode Toggler --> */}
          </ul>
        </div>
      </div>
    </header>
  );
};

export default AuthHeader;
