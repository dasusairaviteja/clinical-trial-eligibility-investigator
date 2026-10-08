const {test,expect}=require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
test('reviewer connects, investigates, corrects, reloads and exports',async({page})=>{
  await page.goto('/');
  await page.getByLabel('Reviewer access token').fill('browser-test-only-token-not-for-deployment');
  await page.getByRole('button',{name:'Connect',exact:true}).click();
  await expect(page.locator('#identity')).toHaveText('Connected as browser-reviewer');
  await expect(page.locator('#status')).toHaveText('Synthetic demo ready.');
  await page.getByRole('button',{name:'Investigate demo case'}).click();
  await expect(page.locator('#results')).toBeVisible();
  await page.getByLabel('Reason',{exact:true}).fill('Browser test: evidence needs review');
  await page.getByRole('button',{name:'Save correction'}).click();
  await expect(page.locator('#criteria')).toContainText('Latest reviewer assertion: unknown');
  await page.getByRole('button',{name:'Refresh saved reports'}).click();
  await expect(page.locator('#history button').first()).toBeVisible();
  const download=page.waitForEvent('download');
  await page.getByRole('button',{name:'Download printable report'}).click();
  expect((await download).suggestedFilename()).toBe('triallens-evidence.html');
  await page.getByRole('button',{name:'Disconnect',exact:true}).click();
  await expect(page.locator('#results')).toBeHidden();
});
test('mobile layout has no horizontal overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  await expect(page.getByRole('heading',{name:'Make every finding traceable.'})).toBeVisible();
});

test('keyboard navigation and automated accessibility scan', async ({page}) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', {name:'Skip to workspace'})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  await page.getByLabel('Reviewer access token').fill('browser-test-only-token-not-for-deployment');
  await page.getByRole('button', {name:'Connect', exact:true}).click();
  await expect(page.locator('#status')).toHaveText('Synthetic demo ready.');
  const scan = async () => {
    const results = await new AxeBuilder({page})
      .withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
    expect(results.violations).toEqual([]);
  };
  await scan();
  await page.getByRole('button', {name:'Investigate demo case'}).click();
  await expect(page.locator('#results')).toBeVisible();
  await scan();
  await page.getByLabel('Reason', {exact:true}).fill('Accessibility test correction');
  await page.getByRole('button', {name:'Save correction'}).click();
  await expect(page.locator('#criteria')).toContainText('Latest reviewer assertion');
  await scan();
});

test('disconnect discards an investigation response already in flight', async ({page}) => {
  await page.goto('/');
  await page.getByLabel('Reviewer access token').fill('browser-test-only-token-not-for-deployment');
  await page.getByRole('button', {name:'Connect', exact:true}).click();
  await expect(page.locator('#status')).toHaveText('Synthetic demo ready.');
  let release;
  let received;
  const ready = new Promise(resolve => { received = resolve; });
  const barrier = new Promise(resolve => { release = resolve; });
  await page.route('**/v1/investigate', async route => {
    const response = await route.fetch();
    received();
    await barrier;
    await route.fulfill({response});
  });
  await page.getByRole('button', {name:'Investigate demo case'}).click();
  await ready;
  await page.getByRole('button', {name:'Disconnect', exact:true}).click();
  release();
  await expect(page.locator('#status')).toContainText('response discarded');
  await expect(page.locator('#results')).toBeHidden();
  await expect(page.locator('#save')).toBeDisabled();
  await expect(page.locator('#request')).toHaveValue('');
});
