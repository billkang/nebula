# 前端测试示例

## 1. 组件测试

```typescript
describe('FormListComponent', () => {
  let fixture: ComponentFixture<FormListComponent>;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      imports: [FormListComponent],
      providers: [provideHttpClient(withInterceptorsFromDi())],
    });
    fixture = TestBed.createComponent(FormListComponent);
  });

  it('should render form list', () => {
    expect(fixture.nativeElement.querySelector('p-table')).toBeTruthy();
  });
});
```

关键点：Standalone 组件直接 `imports: [Component]`；PrimeNG 子组件用 `overrideComponent` 跳过渲染；`provideHttpClientTesting()` + `HttpTestingController` 模拟请求。

## 2. Service 测试

```typescript
describe('FormService', () => {
  let service: FormService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FormService, provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()],
    });
    service = TestBed.inject(FormService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('should GET forms', () => {
    service.list(1).subscribe(res => expect(res.items.length).toBe(2));
    const req = httpMock.expectOne('/api/v1/apps/1/forms');
    expect(req.request.method).toBe('GET');
    req.flush({ items: [{ id: 1 }, { id: 2 }], totalItems: 2 });
  });
});
```

## 3. Unit 测试（Pipe / Signal / E2E）

```typescript
// Pipe — 直接 new 实例，不依赖 TestBed
it('should format LocalDateTime', () => {
  const pipe = new LocalDateTimePipe();
  expect(pipe.transform(LocalDateTime.of(2025, 1, 15, 14, 30), 'yyyy-MM-dd')).toBe('2025-01-15');
});

// Signal
it('should update signal on submit', () => {
  const comp = TestBed.createComponent(MyComponent).componentInstance;
  comp.submit();
  expect(comp.submitted()).toBe(true);
});

// E2E（Playwright）
test('should display form list', async ({ page }) => {
  await page.goto('/apps/1/forms');
  await expect(page.locator('p-table')).toBeVisible();
});
```

## 4. Testing Library 组件测试（推荐方式）

```typescript
import { render, screen, fireEvent } from '@testing-library/angular';

describe('ButtonComponent', () => {
  it('应使用 Testing Library render 渲染组件', async () => {
    await render(ButtonComponent, { inputs: { label: '提交', disabled: false } });
    expect(screen.getByRole('button', { name: '提交' })).toBeTruthy();
  });

  it('disabled 态应不可点击', async () => {
    const onClick = vi.fn();
    await render(ButtonComponent, { inputs: { label: '不可用', disabled: true, onClick } });
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });
});
```

关键点：`render()` 自动处理编译和变更检测；`screen.getByRole()` / `screen.getByText()` 按用户视角查找元素。

## 5. 异步操作测试

```typescript
describe('UserListComponent（异步加载）', () => {
  it('加载完成后应显示用户列表', async () => {
    const mockService = {
      getUsers: vi.fn().mockResolvedValue([{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }]),
    };
    await render(UserListComponent, {
      componentProviders: [{ provide: UserService, useValue: mockService }],
    });
    expect(await screen.findByText('Alice')).toBeTruthy();
    expect(await screen.findByText('Bob')).toBeTruthy();
  });

  it('加载失败时应显示错误提示', async () => {
    await render(UserListComponent, {
      componentProviders: [{ provide: UserService, useValue: { getUsers: vi.fn().mockRejectedValue(new Error('fail')) } }],
    });
    expect(await screen.findByText(/加载失败/i)).toBeTruthy();
  });
});
```

## 6. 带依赖注入的 Service 测试

```typescript
describe('UserService（httpResource）', () => {
  let service: UserService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UserService, provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()],
    });
    service = TestBed.inject(UserService);
  });

  it('应发送带 appId 的 GET 请求', () => {
    const httpMock = TestBed.inject(HttpTestingController);
    service.getUsers(1).subscribe(res => expect(res.items.length).toBe(1));
    const req = httpMock.expectOne('/api/v1/apps/1/users');
    expect(req.request.method).toBe('GET');
    req.flush({ items: [{ id: 1, name: 'Alice' }], totalItems: 1 });
    httpMock.verify();
  });

  it('应发送 POST 请求创建用户', () => {
    const httpMock = TestBed.inject(HttpTestingController);
    service.createUser(1, { name: 'Charlie' }).subscribe();
    const req = httpMock.expectOne('/api/v1/apps/1/users');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Charlie' });
    req.flush({ id: 3, name: 'Charlie' });
    httpMock.verify();
  });
});
```
