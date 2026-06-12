// Theme toggle. The no-flash inline snippet in each page's <head> sets the
// initial theme before paint; this just wires up the button and persistence.
(function () {
  var root = document.documentElement;

  function current() {
    return root.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem("theme", theme); } catch (e) {}
    var btn = document.querySelector(".theme-toggle");
    if (btn) {
      var dark = theme === "dark";
      btn.textContent = dark ? "☀" : "☾";
      btn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    apply(current());
    var btn = document.querySelector(".theme-toggle");
    if (btn) btn.addEventListener("click", function () {
      apply(current() === "dark" ? "light" : "dark");
    });
  });

  // ---- Layout debug guides ----
  // On if the URL ends in #debug; toggle anytime with the "g" key.
  if (location.hash === "#debug") root.classList.add("debug");
  document.addEventListener("keydown", function (e) {
    if (e.key === "g" && !e.metaKey && !e.ctrlKey && !e.altKey &&
        !/^(input|textarea)$/i.test(e.target.tagName)) {
      root.classList.toggle("debug");
    }
  });
})();
