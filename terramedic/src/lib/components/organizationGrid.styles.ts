// Shared layout classes used by OrganizationGrid and
// OrganizationGridSkeleton. Keeping them here prevents the two components
// from drifting and causing a visual reflow when streamed cards replace
// skeletons.
export const ORG_GRID_CONTAINER_CLASS = 'flex flex-wrap justify-center gap-6';
export const ORG_CARD_WRAPPER_CLASS = 'w-full sm:w-72';
