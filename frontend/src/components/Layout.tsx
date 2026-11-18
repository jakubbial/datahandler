import { Outlet } from "react-router-dom";
import TopNavbar from "./TopNavbar";

function Layout() {
  return (
    <>
      <TopNavbar />
      <main className="container py-5">
        <Outlet />
      </main>
    </>
  );
}

export default Layout;
