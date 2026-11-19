(() => {
  const toggle = document.querySelector(".menu-toggle");
  const navigation = document.querySelector("#primary-nav");
  const dropdownToggle = document.querySelector(".nav-dropdown-toggle");
  const dropdownMenu = document.querySelector("#course-topics-menu");
  const callPopup = document.getElementById("call-us-popup");
  const callPopupClose = document.querySelector(".call-popup-close");
  let lastCallTrigger = null;

  if (toggle && navigation) {
    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!expanded));
      navigation.classList.toggle("is-open", !expanded);
    });

    navigation.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        toggle.setAttribute("aria-expanded", "false");
        navigation.classList.remove("is-open");
      });
    });
  }

  if (dropdownToggle && dropdownMenu) {
    const closeDropdown = () => {
      dropdownToggle.setAttribute("aria-expanded", "false");
      dropdownMenu.classList.remove("is-open");
    };

    dropdownToggle.addEventListener("click", () => {
      const expanded = dropdownToggle.getAttribute("aria-expanded") === "true";
      dropdownToggle.setAttribute("aria-expanded", String(!expanded));
      dropdownMenu.classList.toggle("is-open", !expanded);
    });

    dropdownMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeDropdown);
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".nav-dropdown")) {
        closeDropdown();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeDropdown();
        dropdownToggle.focus();
      }
    });
  }

  if (callPopup) {
    const openCallPopup = (trigger) => {
      lastCallTrigger = trigger;
      callPopup.hidden = false;
      document.body.classList.add("modal-open");
      callPopupClose?.focus();
    };

    const closeCallPopup = () => {
      callPopup.hidden = true;
      document.body.classList.remove("modal-open");
      lastCallTrigger?.focus();
    };

    document.querySelectorAll(".call-us-trigger").forEach((trigger) => {
      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        openCallPopup(trigger);
      });
    });

    if (callPopupClose) {
      callPopupClose.addEventListener("click", closeCallPopup);
    }

    callPopup.addEventListener("click", (event) => {
      if (event.target === callPopup) {
        closeCallPopup();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (callPopup.hidden) return;

      if (event.key === "Escape") {
        closeCallPopup();
        return;
      }

      if (event.key === "Tab") {
        const focusable = callPopup.querySelectorAll(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });

    if (!callPopup.hidden) {
      document.body.classList.add("modal-open");
      callPopupClose?.focus();
    }
  }

})();
