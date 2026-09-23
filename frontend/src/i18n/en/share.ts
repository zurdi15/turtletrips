export default {
  section: {
    title: 'Share the trip',
    active: 'This trip has an active read-only public link.',
    inactive: 'Create a link to show the plan to people who do not use the app.',
  },
  link: {
    intro:
      'Anyone with the link sees the plan — no account needed, nothing they can change. Pick what shows up.',
    sections: 'What is visible',
    start: 'Create link',
    save: 'Save changes',
    rotate: 'Regenerate',
    rotateTooltip: 'Creates a new link; the old one stops working',
    stop: 'Stop sharing',
    confirmRotate: 'Regenerate the link? Anyone holding the current one loses access.',
    confirmStop: 'Stop sharing this trip? The link will stop working.',
    copyTooltip: 'Copy the link',
    copied: 'Link copied',
    saveError: 'Could not update the link',
    privacy:
      'Expenses, balances, the budget and booking reference codes never travel.',
    privacyNotes:
      'Notes do not travel either: not on the trip, the activities, the places, nor the diary. Hard facts do: times, routes, flight numbers and the weather forecast.',
  },
  scopes: {
    itinerary: 'Day-by-day itinerary',
    bookings: 'Bookings (no codes, no amounts)',
    map: 'Places and map',
  },
  public: {
    emptyDay: 'Free day',
    placeLink: 'More information',
    errorTitle: 'Could not load the trip',
    errorSubtitle: 'It may be a connection problem. Try again.',
    retry: 'Retry',
    goneTitle: 'This link no longer works',
    goneSubtitle: 'It may have been regenerated, or the trip is no longer shared.',
  },
}
