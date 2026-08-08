/** @odoo-module **/

import { registry } from "@web/core/registry";

const BRAND_NAME = "PassionTech ERP";

function sanitizeTitlePart(value) {
    if (!value) {
        return "";
    }

    return String(value)
        .trim()
        .replace(/^Odoo(?:\s*[-|]\s*)?/i, "")
        .replace(/\s*[-|]\s*Odoo$/i, "")
        .trim();
}

export const passionTechTitleService = {
    start() {
        const titleCounters = {};
        const titleParts = {};

        function getParts() {
            return { ...titleParts };
        }

        function updateTitle() {
            const counter = Object.values(titleCounters).reduce(
                (total, count) => total + count,
                0
            );

            const parts = Object.values(titleParts)
                .map(sanitizeTitlePart)
                .filter(Boolean);

            const context = [...new Set(parts)].join(" - ");

            const name = context
                ? `${context} | ${BRAND_NAME}`
                : BRAND_NAME;

            document.title = counter
                ? `(${counter}) ${name}`
                : name;
        }

        function setCounters(counters) {
            for (const [key, value] of Object.entries(counters)) {
                if (value) {
                    titleCounters[key] = value;
                } else {
                    delete titleCounters[key];
                }
            }
            updateTitle();
        }

        function setParts(parts) {
            for (const [key, value] of Object.entries(parts)) {
                if (value) {
                    titleParts[key] = value;
                } else {
                    delete titleParts[key];
                }
            }
            updateTitle();
        }

        updateTitle();

        return {
            get current() {
                return document.title;
            },
            getParts,
            setCounters,
            setParts,
        };
    },
};

registry.category("services").add("title", passionTechTitleService, {
    force: true,
});
