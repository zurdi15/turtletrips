export default {
  login: {
    title: 'Sign in',
    subtitle: 'Your travel journal awaits.',
    username: 'Username',
    password: 'Password',
    submit: 'Sign in',
    error: 'Could not sign in',
  },
  bootstrap: {
    title: 'Create the admin account',
    hint: 'First run: this account will manage the users and families of the instance.',
    travelerName: 'Your traveler name',
    confirmPassword: 'Repeat the password',
    submit: 'Create account',
    error: 'Could not create the account',
  },
  // recuperación de contraseña: el enlace sale por los logs del servidor y lo
  // reparte el administrador (la app no manda correos)
  forgot: {
    link: 'Forgot your password?',
    title: 'Recover your password',
    hint: 'Enter your username and a link to change it will be generated. Turtle Trips sends no email: the link is written to the server logs.',
    submit: 'Generate the link',
    error: 'Could not generate the link',
    back: 'Back to sign in',
    sent: {
      title: 'Link is on the server',
      body: 'If that account exists, the link is already in the server logs. Ask whoever administers the instance for it and open it before it expires.',
      hasLink: 'I already have the link',
    },
  },
  reset: {
    title: 'Choose a new password',
    checking: 'Checking the link…',
    forUser: "You are changing {username}'s password.",
    submit: 'Save and sign in',
    done: 'Password changed',
    error: 'Could not change the password',
    paste: {
      label: 'Recovery link',
      hint: 'Paste the link that the instance administrator gave you.',
      submit: 'Continue',
    },
    invalid: {
      title: 'Invalid link',
      body: 'The link is not valid or has expired. Links work only once: if you already used it, ask for another one.',
      paste: 'Paste another link',
      retry: 'Request a new link',
    },
  },
  password: {
    current: 'Current password',
    new: 'New password',
    confirm: 'Repeat the new password',
    tooShort: 'The password must be at least 8 characters long',
    mismatch: 'Passwords do not match',
    change: 'Change password',
    changed: 'Password changed',
    changeError: 'Could not change the password',
  },
}
