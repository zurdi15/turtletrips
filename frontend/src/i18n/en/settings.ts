export default {
  title: 'Settings',
  language: {
    title: 'Language',
    hint: 'Interface language.',
  },
  appearance: {
    title: 'Appearance',
    hint: 'Interface theme.',
    light: 'Light',
    dark: 'Dark',
  },
  categories: {
    expense: {
      title: 'Expense categories',
      hint: 'Renaming a category also updates existing expenses.',
    },
    packing: {
      title: 'Packing categories',
      hint: 'Used to group items in packing lists and templates.',
    },
    newPlaceholder: 'New category…',
    confirmDelete: {
      message: 'Delete the "{name}" category? Existing items keep their name.',
      header: 'Delete category',
    },
    toast: {
      colorError: 'Could not change the color',
      addError: 'Could not add',
      renameError: 'Could not rename',
    },
  },
  backup: {
    title: 'Backup',
    hint: 'The backup includes the full database and all attachments.',
    download: 'Download backup',
    restore: 'Restore from backup…',
    confirm: {
      message:
        'This will replace ALL current data (trips, expenses, attachments…) ' +
        'with the contents of the backup. This action cannot be undone.',
      header: 'Restore backup',
      accept: 'Restore',
    },
    toast: {
      restored: 'Backup restored ({n} trips)',
      restoreError: 'Could not restore',
    },
  },
}
