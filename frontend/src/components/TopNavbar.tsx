import { Link, NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/data", label: "Data", end: false },
  { to: "/settings", label: "Settings", end: false },
];

function TopNavbar() {
  return (
    <nav className="navbar navbar-expand bg-body-tertiary border-bottom">
      <div className="container">
        <Link className="navbar-brand fw-semibold text-primary" to="/">
          DataHandler
        </Link>
        <ul className="navbar-nav">
          {navItems.map(({ to, label, end }) => (
            <li className="nav-item" key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  `nav-link${isActive ? " active fw-semibold" : ""}`
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}

export default TopNavbar;
