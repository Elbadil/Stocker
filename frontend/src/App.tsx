import { useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import PageTitle from './components/PageTitle';
import SignIn from './pages/Authentication/SignIn';
import SignUp from './pages/Authentication/SignUp';
import RequestPasswordReset from './pages/Authentication/RequestPasswordReset';
import ResetPassword from './pages/Authentication/ResetPassword';
import Calendar from './pages/Calendar';
import Chart from './pages/Chart';
import ECommerce from './pages/Dashboard/ECommerce';
import FormElements from './pages/Form/FormElements';
import FormLayout from './pages/Form/FormLayout';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import Tables from './pages/Tables';
import Alerts from './pages/UiElements/Alerts';
import Buttons from './pages/UiElements/Buttons';
import DefaultLayout from './layout/DefaultLayout';
import Items from './pages/Inventory/Items';
import Clients from './pages/ClientOrders/Clients/Clients';
import ClientOrders from './pages/ClientOrders/ClientOrders/ClientOrders';
import Suppliers from './pages/SupplierOrders/Suppliers/Suppliers';
import { AuthProvider } from './contexts/AuthContext';
import { AlertProvider } from './contexts/AlertContext';
import { InventoryProvider } from './contexts/InventoryContext';
import { ClientOrdersProvider } from './contexts/ClientOrdersContext';
import { SupplierOrdersProvider } from './contexts/SupplierOrdersContext';

function App() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <AlertProvider>
      <AuthProvider>
        <InventoryProvider>
          <DefaultLayout>
            <Routes>
              <Route
                index
                element={
                  <>
                    <PageTitle title="eCommerce Dashboard | Stocker" />
                    <ECommerce />
                  </>
                }
              />
              {/* Inventory */}
              <Route
                path="/inventory/items"
                element={
                  <>
                    <PageTitle title="Inventory | Stocker" />
                    <Items />
                  </>
                }
              />
              {/* Client Orders */}
              <Route
                path="/client_orders/orders"
                element={
                  <ClientOrdersProvider>
                    <>
                      <PageTitle title="Clients | Stocker" />
                      <ClientOrders />
                    </>
                  </ClientOrdersProvider>
                }
              />
              <Route
                path="/client_orders/clients"
                element={
                  <ClientOrdersProvider>
                    <>
                      <PageTitle title="Client Orders | Stocker" />
                      <Clients />
                    </>
                  </ClientOrdersProvider>
                }
              />
              {/* Supplier Orders */}
              <Route
                path="/supplier_orders/suppliers"
                element={
                  <SupplierOrdersProvider>
                    <>
                      <PageTitle title="Suppliers | Stocker" />
                      <Suppliers />
                    </>
                  </SupplierOrdersProvider>
                }
              />
              {/* Calender */}
              <Route
                path="/calendar"
                element={
                  <>
                    <PageTitle title="Calendar | Stocker" />
                    <Calendar />
                  </>
                }
              />
              <Route
                path="/profile"
                element={
                  <>
                    <PageTitle title="Profile | Stocker" />
                    <Profile />
                  </>
                }
              />
              <Route
                path="/forms/form-elements"
                element={
                  <>
                    <PageTitle title="Form Elements | Stocker" />
                    <FormElements />
                  </>
                }
              />
              <Route
                path="/forms/form-layout"
                element={
                  <>
                    <PageTitle title="Form Layout | Stocker" />
                    <FormLayout />
                  </>
                }
              />
              <Route
                path="/tables"
                element={
                  <>
                    <PageTitle title="Tables | Stocker" />
                    <Tables />
                  </>
                }
              />
              <Route
                path="/settings"
                element={
                  <>
                    <PageTitle title="Settings | Stocker" />
                    <Settings />
                  </>
                }
              />
              <Route
                path="/chart"
                element={
                  <>
                    <PageTitle title="Basic Chart | Stocker" />
                    <Chart />
                  </>
                }
              />
              <Route
                path="/ui/alerts"
                element={
                  <>
                    <PageTitle title="Alerts | Stocker" />
                    <Alerts />
                  </>
                }
              />
              <Route
                path="/ui/buttons"
                element={
                  <>
                    <PageTitle title="Buttons | Stocker" />
                    <Buttons />
                  </>
                }
              />
              {/* Authentication */}
              <Route
                path="/auth/signin"
                element={
                  <>
                    <PageTitle title="Signin | Stocker" />
                    <SignIn />
                  </>
                }
              />
              <Route
                path="/auth/signup"
                element={
                  <>
                    <PageTitle title="Signup | Stocker" />
                    <SignUp />
                  </>
                }
              />
              <Route
                path="/auth/password-reset/request"
                element={
                  <>
                    <PageTitle title="Request Password Reset | Stocker" />
                    <RequestPasswordReset />
                  </>
                }
              />
              <Route
                path="/auth/password-reset/:uidb64/:token"
                element={
                  <>
                    <PageTitle title="Reset Password | Stocker" />
                    <ResetPassword />
                  </>
                }
              />
            </Routes>
          </DefaultLayout>
        </InventoryProvider>
      </AuthProvider>
    </AlertProvider>
  );
}

export default App;
