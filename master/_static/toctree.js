/*
 * toctree.js
 * ~~~~~~~~~~
 *
 * This script makes the table of contents in the sidebar collapsible.
 *
 * It adds a toggle button to each list item containing a nested list.  Clicking a
 * link to a section of the current document toggles its item, too.  Initially,
 * only the items on the path to the current document (marked by Sphinx with the
 * class "current") are expanded.  When jumping to an anchor, the script also
 * expands all items leading to the corresponding sidebar entry.
 */

const initialiseToctree = () => {
  const sidebar = document.querySelector("div.sphinxsidebarwrapper");
  if (!sidebar) return;

  const setExpanded = (item, expanded) => {
    item.classList.toggle("toctree-expanded", expanded);
    const button = item.querySelector(":scope > button.toctree-toggle");
    button.textContent = expanded ? "▾" : "▸";
    button.setAttribute("aria-expanded", expanded);
    for (const list of item.querySelectorAll(":scope > ul")) {
      list.hidden = !expanded;
    }
  };

  for (const item of sidebar.querySelectorAll("li")) {
    if (!item.querySelector(":scope > ul")) continue;
    item.classList.add("toctree-parent");
    const toggle = () =>
      setExpanded(item, !item.classList.contains("toctree-expanded"));
    const button = document.createElement("button");
    button.type = "button";
    button.className = "toctree-toggle";
    button.title = "Expand or collapse";
    button.addEventListener("click", toggle);
    item.prepend(button);
    const link = item.querySelector(":scope > a");
    if (link && link.getAttribute("href").startsWith("#")) {
      link.addEventListener("click", toggle);
    }
    setExpanded(item, item.classList.contains("current"));
  }

  // Expand only the ancestors so that clicking an expanded item collapses it:
  const expandToHash = () => {
    if (!window.location.hash) return;
    for (const link of sidebar.querySelectorAll("a")) {
      if (link.getAttribute("href") !== window.location.hash) continue;
      let item = link.parentElement.parentElement;
      for (; sidebar.contains(item); item = item.parentElement) {
        if (item.classList.contains("toctree-parent")) setExpanded(item, true);
      }
    }
  };
  expandToHash();
  window.addEventListener("hashchange", expandToHash);
};
document.addEventListener("DOMContentLoaded", initialiseToctree);
